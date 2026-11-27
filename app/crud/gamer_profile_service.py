
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from pathlib import Path

from app.models.gamer_profile import GamerProfile
from app.models.user import User
from app.crud.image_upload import save_uploaded_image



AVATAR_DIR = Path(__file__).resolve().parent.parent / "uploads" / "avatars"


def create_profile(db: Session, user_id: int, profile_data):
    existing = get_profile_by_user_id(db, user_id)
    if existing:
        raise HTTPException(status_code=409, detail="Hồ sơ game thủ đã tồn tại")

    display_name = profile_data.display_name.strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="Tên hiển thị không được để trống")

    profile = GamerProfile(
        user_id=user_id,
        display_name=display_name,
        bio=profile_data.bio,
        region=profile_data.region,
        play_time=profile_data.play_time,
        has_mic=profile_data.has_mic,
        is_public=profile_data.is_public,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


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

    filename = await save_uploaded_image(file, AVATAR_DIR)
    file_path = AVATAR_DIR / filename

    try:
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
