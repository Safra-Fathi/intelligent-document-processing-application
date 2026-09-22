from pathlib import Path
from typing import Any

from app.pipeline.classifier import classifier
from app.pipeline.extractor import extract_fields
from app.pipeline.ocr import extract_text
from app.pipeline.validator import validate_document


PIPELINE_VERSION = "pipeline-v2"


def process_document(
    file_path: Path,
    mime_type: str,
) -> dict[str, Any]:
    # -----------------------------------------------------
    # 1. OCR / text acquisition
    # -----------------------------------------------------

    text = extract_text(
        file_path,
        mime_type,
    )

    if not text.strip():
        raise ValueError(
            "No readable text could be extracted "
            "from the document."
        )

    # -----------------------------------------------------
    # 2. Document classification
    # -----------------------------------------------------

    classification = classifier.predict(
        text
    )

    predicted_type = classification[
        "predicted_type"
    ]

    classification_confidence = classification[
        "confidence"
    ]

    # -----------------------------------------------------
    # 3. Structured information extraction
    # -----------------------------------------------------

    fields = extract_fields(
        text,
        predicted_type,
    )

    # -----------------------------------------------------
    # 4. Business validation + review routing
    # -----------------------------------------------------

    issues, review_status = validate_document(
        fields=fields,
        document_type=predicted_type,
        classification_confidence=(
            classification_confidence
        ),
    )

    # -----------------------------------------------------
    # 5. Return pipeline result
    # Persistence remains outside the ML pipeline.
    # -----------------------------------------------------

    return {
        "predicted_type": predicted_type,
        "classification_confidence": (
            classification_confidence
        ),
        "classifier_version": classification[
            "classifier_version"
        ],
        "pipeline_version": PIPELINE_VERSION,
        "review_status": review_status,
        "fields": fields,
        "validation_issues": issues,
    }