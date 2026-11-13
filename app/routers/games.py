from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.game import Game
from app.schemas.game import GameCatalogResponse

router = APIRouter(prefix="/api/games", tags=["Games Catalog"])


@router.get("", response_model=list[GameCatalogResponse])
def get_games_catalog(db: Session = Depends(get_db)):
    """Danh mục game để frontend hiển thị lựa chọn game, rank và role."""
    return (
        db.query(Game)
        .options(joinedload(Game.ranks), joinedload(Game.roles))
        .order_by(Game.name.asc())
        .all()
    )


@router.get("/{game_id}", response_model=GameCatalogResponse)
def get_game_detail(game_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    game = (
        db.query(Game)
        .options(joinedload(Game.ranks), joinedload(Game.roles))
        .filter(Game.id == game_id)
        .first()
    )
    if game is None:
        raise HTTPException(status_code=404, detail="Game không tồn tại")
    return game
