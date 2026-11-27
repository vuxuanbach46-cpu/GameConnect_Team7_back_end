from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.user_game import UserGameCreate, UserGameUpdate, UserGameResponse
from app.crud.user_game_service import (
    get_my_games,
    add_favorite_game,
    update_favorite_game,
    delete_favorite_game,
)

router = APIRouter(prefix="/api/user-games", tags=["User Favorite Games"])


@router.get("/me", response_model=list[UserGameResponse])
def read_my_favorite_games(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_my_games(db, current_user.id)


@router.post("/me", response_model=UserGameResponse, status_code=status.HTTP_201_CREATED)
def create_my_favorite_game(
    data: UserGameCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return add_favorite_game(db, current_user.id, data)


@router.put("/me/{user_game_id}", response_model=UserGameResponse)
def edit_my_favorite_game(
    user_game_id: int,
    data: UserGameUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_favorite_game(db, current_user.id, user_game_id, data)


@router.delete("/me/{user_game_id}")
def remove_my_favorite_game(
    user_game_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_favorite_game(db, current_user.id, user_game_id)
