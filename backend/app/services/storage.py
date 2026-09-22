from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

PDF_SIGNATURE = b"%PDF-"


async def validate_and_store_file(file: UploadFile) -> tuple[str, int]:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, PNG, JPG, and JPEG files are allowed.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 10 MB upload limit.",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    extension = ALLOWED_TYPES[file.content_type]

    # Validate actual file content rather than trusting MIME type alone.
    if file.content_type == "application/pdf":
        if not content.startswith(PDF_SIGNATURE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is not a valid PDF.",
            )
    else:
        _validate_image(content, file.content_type)

    stored_filename = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / stored_filename

    try:
        destination.write_bytes(content)
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store uploaded file.",
        )

    return stored_filename, len(content)


def _validate_image(content: bytes, content_type: str) -> None:
    from io import BytesIO

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()

            actual_format = image.format

            if content_type == "image/png" and actual_format != "PNG":
                raise ValueError

            if content_type == "image/jpeg" and actual_format != "JPEG":
                raise ValueError

    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image is invalid or does not match its file type.",
        )


def delete_stored_file(stored_filename: str) -> None:
    file_path = UPLOAD_DIR / stored_filename

    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass