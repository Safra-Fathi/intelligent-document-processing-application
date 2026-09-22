from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    mime_type: str
    size_bytes: int
    processing_status: str
    predicted_type: str | None
    classification_confidence: float | None
    review_status: str | None
    pipeline_version: str | None
    classifier_version: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExtractedFieldResponse(BaseModel):
    id: int
    field_name: str
    original_value: str | None
    confidence: float | None

    # Latest human correction, if one exists.
    corrected_value: str | None = None
    correction_reason: str | None = None
    corrected_at: datetime | None = None
    corrected_by_user_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

class ValidationIssueResponse(BaseModel):
    id: int
    field_name: str | None
    issue_code: str
    severity: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class DocumentProcessingResponse(BaseModel):
    document: DocumentResponse
    fields: list[ExtractedFieldResponse]
    validation_issues: list[ValidationIssueResponse]


class CorrectionCreate(BaseModel):
    corrected_value: str = Field(
        min_length=1,
        max_length=2000,
    )
    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class CorrectionResponse(BaseModel):
    id: int
    extracted_field_id: int
    user_id: int
    corrected_value: str
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseModel):
    id: int
    document_id: int
    user_id: int | None
    event_type: str
    details: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)