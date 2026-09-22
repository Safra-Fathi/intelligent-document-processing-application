from io import BytesIO
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

from app.core.config import settings
from app.pipeline.preprocessing import preprocess_image


# Tell pytesseract where the Windows Tesseract executable is located.
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def extract_text(file_path: Path, mime_type: str) -> str:
    """
    Extract machine-readable text from a supported document.

    Digital PDFs:
        Use their embedded text layer first.

    Scanned PDFs:
        Render pages as images and use OCR.

    PNG/JPEG:
        Preprocess the image and use OCR.
    """

    if mime_type == "application/pdf":
        return _extract_from_pdf(file_path)

    if mime_type in {"image/png", "image/jpeg"}:
        return _extract_from_image(file_path)

    raise ValueError(
        f"Unsupported document type: {mime_type}"
    )


def _extract_from_image(file_path: Path) -> str:
    """
    Extract text from an image using Tesseract OCR.
    """

    with Image.open(file_path) as image:
        processed_image = preprocess_image(image)

        text = pytesseract.image_to_string(
            processed_image,
            lang="eng",
        )

        return text.strip()


def _extract_from_pdf(file_path: Path) -> str:
    """
    Extract text from a PDF.

    Native PDF text extraction is attempted first.
    If insufficient text is available, OCR is used.
    """

    document = fitz.open(file_path)

    try:
        # First try extracting the PDF's embedded text.
        native_text = "\n".join(
            page.get_text("text")
            for page in document
        ).strip()

        # If the PDF already contains meaningful text,
        # OCR is unnecessary.
        if len(native_text) >= 30:
            return native_text

        # Otherwise assume this may be a scanned PDF.
        ocr_pages: list[str] = []

        for page in document:
            # Render at approximately 2x resolution
            # to improve OCR quality.
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image = Image.open(
                BytesIO(pixmap.tobytes("png"))
            )

            processed_image = preprocess_image(image)

            page_text = pytesseract.image_to_string(
                processed_image,
                lang="eng",
            )

            ocr_pages.append(page_text)

        return "\n".join(ocr_pages).strip()

    finally:
        document.close()
        