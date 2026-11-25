from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile


MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": (".jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (
        ".webp",
        lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
    ),
}


async def save_uploaded_image(file: UploadFile, destination: Path) -> str:
    content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    image_type = ALLOWED_IMAGE_TYPES.get(content_type)
    if image_type is None:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận JPG, PNG hoặc WEBP")

    content = await file.read(MAX_IMAGE_SIZE + 1)
    if not content:
        raise HTTPException(status_code=400, detail="File ảnh không được để trống")
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Dung lượng ảnh tối đa là 5MB")
    if not image_type[1](content):
        raise HTTPException(status_code=400, detail="Nội dung file không đúng định dạng ảnh")

    destination.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{image_type[0]}"
    file_path = destination / filename
    try:
        file_path.write_bytes(content)
    except OSError as error:
        raise HTTPException(
            status_code=500, detail="Không thể lưu ảnh đã tải lên"
        ) from error
    return filename
