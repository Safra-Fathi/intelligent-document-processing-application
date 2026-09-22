from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.audit_event import AuditEvent
from app.models.correction import Correction
from app.models.document import Document
from app.models.extracted_field import ExtractedField
from app.models.user import User
from app.models.validation_issue import ValidationIssue
from app.pipeline.processor import process_document
from app.schemas.document import (
    AuditEventResponse,
    CorrectionCreate,
    CorrectionResponse,
    DocumentProcessingResponse,
    DocumentResponse,
)
from app.services.storage import (
    UPLOAD_DIR,
    delete_stored_file,
    validate_and_store_file,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ---------------------------------------------------------
# Upload document
# ---------------------------------------------------------

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    original_filename = file.filename or "unnamed"

    stored_filename, size_bytes = await validate_and_store_file(file)

    document = Document(
        user_id=current_user.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        processing_status="UPLOADED",
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()
        delete_stored_file(stored_filename)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create document record.",
        )

    return document


# ---------------------------------------------------------
# Get current user's documents
# ---------------------------------------------------------

@router.get(
    "",
    response_model=list[DocumentResponse],
)
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = db.scalars(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    ).all()

    return documents


# ---------------------------------------------------------
# Get one document
# ---------------------------------------------------------

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document

# ---------------------------------------------------------
# Get original uploaded file for preview
# Protected by document ownership
# ---------------------------------------------------------

@router.get("/{document_id}/file")
def get_document_file(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify that the authenticated user owns the document.
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Resolve the private stored file.
    file_path = Path(UPLOAD_DIR) / document.stored_filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file was not found.",
        )

    # Serve inline so the frontend can display PDFs/images
    # without exposing the private upload directory directly.
    return FileResponse(
        path=file_path,
        media_type=document.mime_type,
        filename=document.original_filename,
        content_disposition_type="inline",
    )
# ---------------------------------------------------------
# Process uploaded document
# OCR -> classification -> extraction -> validation
# ---------------------------------------------------------

@router.post(
    "/{document_id}/process",
    response_model=DocumentProcessingResponse,
)
def process_uploaded_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    file_path = Path(UPLOAD_DIR) / document.stored_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file was not found.",
        )

    document.processing_status = "PROCESSING"

    db.add(
        AuditEvent(
            document_id=document.id,
            user_id=current_user.id,
            event_type="PROCESSING_STARTED",
            details="Document processing started.",
        )
    )

    db.commit()

    try:
        result = process_document(
            file_path=file_path,
            mime_type=document.mime_type,
        )

        # Remove previous extraction results if reprocessed.
        previous_fields = db.scalars(
            select(ExtractedField).where(
                ExtractedField.document_id == document.id
            )
        ).all()

        for field in previous_fields:
            db.delete(field)

        previous_issues = db.scalars(
            select(ValidationIssue).where(
                ValidationIssue.document_id == document.id
            )
        ).all()

        for issue in previous_issues:
            db.delete(issue)

        db.flush()

        # Save extracted fields.
        field_records = []

        for field in result["fields"]:
            record = ExtractedField(
                document_id=document.id,
                field_name=field["field_name"],
                original_value=field["value"],
                confidence=field["confidence"],
            )

            db.add(record)
            field_records.append(record)

        # Save validation issues.
        issue_records = []

        for issue in result["validation_issues"]:
            record = ValidationIssue(
                document_id=document.id,
                field_name=issue["field_name"],
                issue_code=issue["issue_code"],
                severity=issue["severity"],
                message=issue["message"],
            )

            db.add(record)
            issue_records.append(record)

        # Update document processing result.
        document.predicted_type = result["predicted_type"]
        document.classification_confidence = result[
            "classification_confidence"
        ]
        document.review_status = result["review_status"]
        document.pipeline_version = result["pipeline_version"]
        document.classifier_version = result["classifier_version"]
        document.processing_status = "COMPLETED"
        document.error_message = None

        db.add(
            AuditEvent(
                document_id=document.id,
                user_id=current_user.id,
                event_type="PROCESSING_COMPLETED",
                details=(
                    f"Type={document.predicted_type}; "
                    f"confidence={document.classification_confidence}; "
                    f"review={document.review_status}"
                ),
            )
        )

        db.commit()

        for record in field_records:
            db.refresh(record)

        for record in issue_records:
            db.refresh(record)

        db.refresh(document)

        return {
            "document": document,
            "fields": field_records,
            "validation_issues": issue_records,
        }

    except Exception as exc:
        db.rollback()

        document = db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == current_user.id,
            )
        )

        if document is not None:
            document.processing_status = "FAILED"
            document.error_message = str(exc)[:500]

            db.add(
                AuditEvent(
                    document_id=document.id,
                    user_id=current_user.id,
                    event_type="PROCESSING_FAILED",
                    details=str(exc)[:500],
                )
            )

            db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document processing failed.",
        )


# ---------------------------------------------------------
# Get complete processing result
# Includes latest human correction for each field
# ---------------------------------------------------------

@router.get(
    "/{document_id}/result",
    response_model=DocumentProcessingResponse,
)
def get_document_result(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ownership check.
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    fields = db.scalars(
        select(ExtractedField)
        .where(
            ExtractedField.document_id == document.id
        )
        .order_by(ExtractedField.id)
    ).all()

    field_results = []

    for field in fields:
        # A field may have several historical corrections.
        # The result screen displays the newest one.
        latest_correction = db.scalar(
            select(Correction)
            .where(
                Correction.extracted_field_id == field.id
            )
            .order_by(
                Correction.created_at.desc(),
                Correction.id.desc(),
            )
            .limit(1)
        )

        field_results.append(
            {
                "id": field.id,
                "field_name": field.field_name,
                "original_value": field.original_value,
                "confidence": field.confidence,

                # Human correction information.
                "corrected_value": (
                    latest_correction.corrected_value
                    if latest_correction
                    else None
                ),
                "correction_reason": (
                    latest_correction.reason
                    if latest_correction
                    else None
                ),
                "corrected_at": (
                    latest_correction.created_at
                    if latest_correction
                    else None
                ),
                "corrected_by_user_id": (
                    latest_correction.user_id
                    if latest_correction
                    else None
                ),
            }
        )

    validation_issues = db.scalars(
        select(ValidationIssue)
        .where(
            ValidationIssue.document_id == document.id
        )
        .order_by(ValidationIssue.id)
    ).all()

    return {
        "document": document,
        "fields": field_results,
        "validation_issues": validation_issues,
    }


# ---------------------------------------------------------
# Create human correction for an extracted field
# ---------------------------------------------------------

@router.post(
    "/{document_id}/fields/{field_id}/corrections",
    response_model=CorrectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_field_correction(
    document_id: int,
    field_id: int,
    correction_data: CorrectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify document ownership.
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Verify that the field belongs to this document.
    extracted_field = db.scalar(
        select(ExtractedField).where(
            ExtractedField.id == field_id,
            ExtractedField.document_id == document.id,
        )
    )

    if extracted_field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extracted field not found.",
        )

    corrected_value = correction_data.corrected_value.strip()

    if not corrected_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Corrected value cannot be empty.",
        )

    reason = None

    if correction_data.reason:
        reason = correction_data.reason.strip() or None

    # Store correction separately.
    # Never overwrite ExtractedField.original_value.
    correction = Correction(
        extracted_field_id=extracted_field.id,
        user_id=current_user.id,
        corrected_value=corrected_value,
        reason=reason,
    )

    db.add(correction)

    db.add(
        AuditEvent(
            document_id=document.id,
            user_id=current_user.id,
            event_type="FIELD_CORRECTED",
            details=(
                f"Field={extracted_field.field_name}; "
                f"original={extracted_field.original_value}; "
                f"corrected={corrected_value}"
            ),
        )
    )

    db.commit()
    db.refresh(correction)

    return correction


# ---------------------------------------------------------
# Get document audit history
# ---------------------------------------------------------

@router.get(
    "/{document_id}/audit",
    response_model=list[AuditEventResponse],
)
def get_document_audit_history(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Ownership check before exposing private audit data.
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    events = db.scalars(
        select(AuditEvent)
        .where(
            AuditEvent.document_id == document.id
        )
        .order_by(
            AuditEvent.created_at.asc(),
            AuditEvent.id.asc(),
        )
    ).all()

    return events