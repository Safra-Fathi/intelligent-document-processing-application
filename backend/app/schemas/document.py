from datetime import datetime

from pydantic import BaseModel, ConfigDict


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