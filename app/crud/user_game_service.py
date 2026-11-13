from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.models.user_game import UserGame
from app.models.user import User

MAX_FAVORITE_GAMES = 5


def _validate_game_options(db: Session, game_id: int, rank_id=None, role_id=None):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game is None:
        raise HTTPException(status_code=404, detail="Game không tồn tại")

    if rank_id is not None:
        rank = db.query(GameRank).filter(GameRank.id == rank_id).first()
        if rank is None:
            raise HTTPException(status_code=404, detail="Rank không tồn tại")
        if rank.game_id != game_id:
            raise HTTPException(status_code=400, detail="Rank không thuộc game đã chọn")

    if role_id is not None:
        role = db.query(GameRole).filter(GameRole.id == role_id).first()
        if role is None:
            raise HTTPException(status_code=404, detail="Role không tồn tại")
        if role.game_id != game_id:
            raise HTTPException(status_code=400, detail="Role không thuộc game đã chọn")
    return game


def get_my_games(db: Session, user_id: int):
    return (
        db.query(UserGame)
        .options(joinedload(UserGame.game), joinedload(UserGame.rank), joinedload(UserGame.role))
        .filter(UserGame.user_id == user_id)
        .order_by(UserGame.created_at.asc(), UserGame.id.asc())
        .all()
    )


def add_favorite_game(db: Session, user_id: int, data):
    # Khóa dòng user để hai request thêm đồng thời không vượt quá giới hạn 5.
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if user is None:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    _validate_game_options(db, data.game_id, data.rank_id, data.role_id)

    exists = db.query(UserGame).filter(
        UserGame.user_id == user_id,
        UserGame.game_id == data.game_id,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Game đã có trong danh sách yêu thích")

    count = db.query(UserGame).filter(UserGame.user_id == user_id).count()
    if count >= MAX_FAVORITE_GAMES:
        raise HTTPException(status_code=400, detail="Mỗi tài khoản chỉ được chọn tối đa 5 game")

    item = UserGame(
        user_id=user_id,
        game_id=data.game_id,
        rank_id=data.rank_id,
        role_id=data.role_id,
        in_game_id=data.in_game_id.strip() if data.in_game_id else None,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Game đã tồn tại hoặc dữ liệu tham chiếu không hợp lệ")
    db.refresh(item)
    return (
        db.query(UserGame)
        .options(joinedload(UserGame.game), joinedload(UserGame.rank), joinedload(UserGame.role))
        .filter(UserGame.id == item.id, UserGame.user_id == user_id)
        .first()
    )


def update_favorite_game(db: Session, user_id: int, user_game_id: int, data):
    item = db.query(UserGame).filter(
        UserGame.id == user_game_id,
        UserGame.user_id == user_id,
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy game yêu thích")

    values = data.model_dump(exclude_unset=True)
    rank_id = values.get("rank_id", item.rank_id)
    role_id = values.get("role_id", item.role_id)
    _validate_game_options(db, item.game_id, rank_id, role_id)

    for key, value in values.items():
        if key == "in_game_id" and value is not None:
            value = value.strip() or None
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return (
        db.query(UserGame)
        .options(joinedload(UserGame.game), joinedload(UserGame.rank), joinedload(UserGame.role))
        .filter(UserGame.id == item.id, UserGame.user_id == user_id)
        .first()
    )


def delete_favorite_game(db: Session, user_id: int, user_game_id: int):
    item = db.query(UserGame).filter(
        UserGame.id == user_game_id,
        UserGame.user_id == user_id,
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy game yêu thích")
    db.delete(item)
    db.commit()
    return {"message": "Đã xóa game khỏi danh sách yêu thích"}
