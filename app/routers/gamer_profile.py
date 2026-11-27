from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from app.models.friendships import Friendship
from app.models.friend_request import FriendRequest
from app.schemas.gamer_profile import (
    GamerProfileCreate,
    GamerProfileUpdate,
    GamerProfileResponse,
    PublicGamerProfileResponse,
)
from app.crud.gamer_profile_service import (
    create_profile,
    get_profile_by_user_id,
    get_profile_by_username,
    update_profile,
    upload_avatar,
)
from app.crud.user_game_service import get_my_games
from app.crud.team_join import get_user_teams

router = APIRouter(prefix="/api/profiles", tags=["Gamer Profiles"])


@router.get("/me", response_model=GamerProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Bạn chưa có hồ sơ game thủ")
    return profile


@router.post("/me", response_model=GamerProfileResponse, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    profile_data: GamerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_profile(db, current_user.id, profile_data)


@router.get("/{username}", response_model=PublicGamerProfileResponse)
def get_public_profile(
    username: str,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    profile, resolved_username = get_profile_by_username(db, username)

    if not getattr(profile, "is_public", False):
        raise HTTPException(status_code=403, detail="Hồ sơ này không được công khai")

    friend_status = "NONE"
    if current_user:
        if current_user.id == profile.user_id:
            friend_status = "SELF"
        else:
            user_a, user_b = sorted((current_user.id, profile.user_id))
            friendship = db.query(Friendship).filter(
                Friendship.user_a == user_a,
                Friendship.user_b == user_b,
            ).first()
            if friendship:
                friend_status = "FRIEND"
            else:
                outgoing = db.query(FriendRequest).filter(
                    FriendRequest.sender_id == current_user.id,
                    FriendRequest.receiver_id == profile.user_id,
                    FriendRequest.status == "PENDING",
                ).first()
                incoming = db.query(FriendRequest).filter(
                    FriendRequest.sender_id == profile.user_id,
                    FriendRequest.receiver_id == current_user.id,
                    FriendRequest.status == "PENDING",
                ).first()
                if outgoing:
                    friend_status = "SENT"
                elif incoming:
                    friend_status = "RECEIVED"

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "username": resolved_username,
        "display_name": profile.display_name,
        "avatar": profile.avatar,
        "bio": profile.bio,
        "region": profile.region,
        "play_time": profile.play_time,
        "has_mic": profile.has_mic,
        "is_public": profile.is_public,
        "friend_status": friend_status,
        "user_games": get_my_games(db, profile.user_id),
        "teams": get_user_teams(db, profile.user_id),
    }


@router.put("/me", response_model=GamerProfileResponse)
def update_my_profile(
    profile_data: GamerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_profile(db, current_user.id, profile_data)


@router.post("/me/avatar", response_model=GamerProfileResponse)
async def update_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await upload_avatar(db, current_user.id, file)
