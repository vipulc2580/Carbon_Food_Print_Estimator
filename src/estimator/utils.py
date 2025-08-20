from fastapi import UploadFile, File, HTTPException, status
from typing import Literal
from .schemas import ValidatedImage
import base64

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

async def validate_image(file: UploadFile = File(...)) -> ValidatedImage:
    
    contents = await file.read()
    size_bytes = len(contents)
    file.file.seek(0)
    if size_bytes > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image too large. Max allowed: 5MB, got {round(size_bytes/1024/1024,2)}MB"
        )

    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format {file.content_type}. Allowed: {allowed_types}"
        )

    image_b64 = base64.b64encode(contents).decode("utf-8")

    return ValidatedImage(
        filename=file.filename,
        size_bytes=size_bytes,
        content_type=file.content_type,
        image_b64=image_b64
    )

