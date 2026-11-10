
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user

from app.schemas.gamer_profile import (
    GamerProfileUpdate,
    GamerProfileResponse,
    PublicGamerProfileResponse
)

from app.crud.gamer_profile_service import (
    get_profile_by_user_id,
    get_profile_by_username,
    update_profile,
    upload_avatar
)


router = APIRouter(
    prefix="/api/profiles",
    tags=["Gamer Profiles"]
)


# 1. GET: Lấy hồ sơ cá nhân
@router.get(
    "/me",
    response_model=GamerProfileResponse
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    profile = get_profile_by_user_id(
        db,
        current_user.id
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Bạn chưa có hồ sơ game thủ"
        )

    return profile


# 2. GET: Lấy hồ sơ theo username
@router.get(
    "/{username}",
    response_model=PublicGamerProfileResponse
)
def get_public_profile(
    username: str,
    db: Session = Depends(get_db)
):
    profile, username = get_profile_by_username(
        db,
        username
    )

    # Mặc định từ chối công khai nếu chưa có
    # trường is_public trong model.
    if not getattr(profile, "is_public", False):
        raise HTTPException(
            status_code=403,
            detail="Hồ sơ này không được công khai"
        )

    return {
        "id": profile.id,
        "username": username,
        "display_name": profile.display_name,
        "avatar": profile.avatar,
        "bio": profile.bio,
        "region": profile.region,
        "play_time": profile.play_time,
        "has_mic": profile.has_mic
    }


# 3. PUT: Cập nhật hồ sơ cá nhân
@router.put(
    "/me",
    response_model=GamerProfileResponse
)
def update_my_profile(
    profile_data: GamerProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return update_profile(
        db,
        current_user.id,
        profile_data
    )


# 4. POST: Upload avatar
@router.post(
    "/me/avatar",
    response_model=GamerProfileResponse
)
async def update_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await upload_avatar(
        db,
        current_user.id,
        file
    )
