
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from pathlib import Path
from uuid import uuid4

from app.models.gamer_profile import GamerProfile
from app.models.user import User

import os


AVATAR_DIR = Path("app/uploads/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024

ALLOWED_IMAGES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}

IMAGE_SIGNATURES = {
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "image/png": lambda data: data.startswith(
        b"\x89PNG\r\n\x1a\n"
    ),
    "image/webp": lambda data: (
        len(data) >= 12
        and data[:4] == b"RIFF"
        and data[8:12] == b"WEBP"
    )
}


def get_profile_by_user_id(db: Session, user_id: int):
    return db.query(GamerProfile).filter(
        GamerProfile.user_id == user_id
    ).first()


def get_profile_by_username(db: Session, username: str):
    result = (
        db.query(GamerProfile, User.username)
        .join(User, GamerProfile.user_id == User.id)
        .filter(User.username == username)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy hồ sơ người dùng"
        )

    profile, username = result
    return profile, username


def update_profile(
    db: Session,
    user_id: int,
    profile_data
):
    profile = get_profile_by_user_id(db, user_id)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Hồ sơ không tồn tại"
        )

    update_data = profile_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        if key == "display_name" and value is not None:
            value = value.strip()

            if not value:
                raise HTTPException(
                    status_code=400,
                    detail="Tên hiển thị không được để trống"
                )

        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return profile


async def upload_avatar(
    db: Session,
    user_id: int,
    file: UploadFile
):
    profile = get_profile_by_user_id(db, user_id)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Hồ sơ không tồn tại"
        )

    content_type = file.content_type

    if content_type not in ALLOWED_IMAGES:
        raise HTTPException(
            status_code=400,
            detail="Chỉ chấp nhận JPG, PNG hoặc WEBP"
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="File ảnh không được để trống"
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Dung lượng ảnh tối đa là 5MB"
        )

    if not IMAGE_SIGNATURES[content_type](content):
        raise HTTPException(
            status_code=400,
            detail="Nội dung file không đúng định dạng ảnh"
        )

    extension = ALLOWED_IMAGES[content_type]
    filename = f"{uuid4().hex}{extension}"

    file_path = AVATAR_DIR / filename

    try:
        with open(file_path, "wb") as f:
            f.write(content)

        old_avatar = profile.avatar

        profile.avatar = f"/uploads/avatars/{filename}"

        db.commit()
        db.refresh(profile)

    except Exception:
        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Không thể cập nhật ảnh đại diện"
        )

    # Xóa avatar cũ nếu đó là file thuộc thư mục upload.
    if old_avatar and old_avatar.startswith(
        "/uploads/avatars/"
    ):
        old_path = (
            AVATAR_DIR / Path(old_avatar).name
        )

        if old_path.exists() and old_path != file_path:
            old_path.unlink()

    return profile
