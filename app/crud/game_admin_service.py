from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole


def _not_found(message):
    raise HTTPException(status_code=404, detail=message)


def _required_text(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise HTTPException(status_code=400, detail=f"{field_name} không được để trống")
    return value


def list_games(db: Session):
    return db.query(Game).options(joinedload(Game.ranks), joinedload(Game.roles)).order_by(Game.name).all()


def get_game(db: Session, game_id: int):
    game = db.query(Game).options(joinedload(Game.ranks), joinedload(Game.roles)).filter(Game.id == game_id).first()
    if game is None:
        _not_found("Game không tồn tại")
    return game


def create_game(db: Session, data):
    game = Game(name=_required_text(data.name, "Tên game"), image=data.image, genre=_required_text(data.genre, "Thể loại"))
    db.add(game)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tên game đã tồn tại")
    db.refresh(game)
    return game


def update_game(db: Session, game_id: int, data):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game is None:
        _not_found("Game không tồn tại")
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "name" and value is not None:
            value = _required_text(value, "Tên game")
        if key == "genre" and value is not None:
            value = _required_text(value, "Thể loại")
        setattr(game, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tên game đã tồn tại")
    db.refresh(game)
    return game


def delete_game(db: Session, game_id: int):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game is None:
        _not_found("Game không tồn tại")
    db.delete(game)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Không thể xóa game do đang được dữ liệu khác sử dụng")
    return {"message": "Đã xóa game"}


def list_game_ranks(db: Session, game_id: int):
    if db.query(Game.id).filter(Game.id == game_id).first() is None:
        _not_found("Game không tồn tại")
    return db.query(GameRank).filter(GameRank.game_id == game_id).order_by(GameRank.rank_order, GameRank.id).all()


def create_game_rank(db: Session, game_id: int, data):
    if db.query(Game.id).filter(Game.id == game_id).first() is None:
        _not_found("Game không tồn tại")
    obj = GameRank(game_id=game_id, rank_name=_required_text(data.rank_name, "Tên rank"), rank_order=data.rank_order)
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Rank này đã tồn tại trong game")
    db.refresh(obj)
    return obj


def update_game_rank(db: Session, rank_id: int, data):
    obj = db.query(GameRank).filter(GameRank.id == rank_id).first()
    if obj is None:
        _not_found("Rank không tồn tại")
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "rank_name" and value is not None:
            value = _required_text(value, "Tên rank")
        setattr(obj, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Rank này đã tồn tại trong game")
    db.refresh(obj)
    return obj


def delete_game_rank(db: Session, rank_id: int):
    obj = db.query(GameRank).filter(GameRank.id == rank_id).first()
    if obj is None:
        _not_found("Rank không tồn tại")
    db.delete(obj)
    db.commit()
    return {"message": "Đã xóa rank"}


def list_game_roles(db: Session, game_id: int):
    if db.query(Game.id).filter(Game.id == game_id).first() is None:
        _not_found("Game không tồn tại")
    return db.query(GameRole).filter(GameRole.game_id == game_id).order_by(GameRole.role_name).all()


def create_game_role(db: Session, game_id: int, data):
    if db.query(Game.id).filter(Game.id == game_id).first() is None:
        _not_found("Game không tồn tại")
    obj = GameRole(game_id=game_id, role_name=_required_text(data.role_name, "Tên role"))
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Role này đã tồn tại trong game")
    db.refresh(obj)
    return obj


def update_game_role(db: Session, role_id: int, data):
    obj = db.query(GameRole).filter(GameRole.id == role_id).first()
    if obj is None:
        _not_found("Role không tồn tại")
    values = data.model_dump(exclude_unset=True)
    if "role_name" in values and values["role_name"] is not None:
        obj.role_name = _required_text(values["role_name"], "Tên role")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Role này đã tồn tại trong game")
    db.refresh(obj)
    return obj


def delete_game_role(db: Session, role_id: int):
    obj = db.query(GameRole).filter(GameRole.id == role_id).first()
    if obj is None:
        _not_found("Role không tồn tại")
    db.delete(obj)
    db.commit()
    return {"message": "Đã xóa role"}
