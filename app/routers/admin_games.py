from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.db.session import get_db
from app.schemas.game import GameCreate, GameUpdate, GameResponse, GameCatalogResponse
from app.schemas.game_rank import GameRankCreate, GameRankUpdate, GameRankResponse
from app.schemas.game_role import GameRoleCreate, GameRoleUpdate, GameRoleResponse
from app.crud import game_admin_service as service

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin - Game Catalog"],
    dependencies=[Depends(get_current_user), Depends(require_admin)],
)


# GAME CRUD
@router.get("/games", response_model=list[GameCatalogResponse])
def admin_list_games(db: Session = Depends(get_db)):
    return service.list_games(db)


@router.post("/games", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def admin_create_game(data: GameCreate, db: Session = Depends(get_db)):
    return service.create_game(db, data)


@router.put("/games/{game_id}", response_model=GameResponse)
def admin_update_game(game_id: int, data: GameUpdate, db: Session = Depends(get_db)):
    return service.update_game(db, game_id, data)


@router.delete("/games/{game_id}")
def admin_delete_game(game_id: int, db: Session = Depends(get_db)):
    return service.delete_game(db, game_id)


# RANK CRUD
@router.get("/games/{game_id}/ranks", response_model=list[GameRankResponse])
def admin_list_ranks(game_id: int, db: Session = Depends(get_db)):
    return service.list_game_ranks(db, game_id)


@router.post("/games/{game_id}/ranks", response_model=GameRankResponse, status_code=status.HTTP_201_CREATED)
def admin_create_rank(game_id: int, data: GameRankCreate, db: Session = Depends(get_db)):
    return service.create_game_rank(db, game_id, data)


@router.put("/game-ranks/{rank_id}", response_model=GameRankResponse)
def admin_update_rank(rank_id: int, data: GameRankUpdate, db: Session = Depends(get_db)):
    return service.update_game_rank(db, rank_id, data)


@router.delete("/game-ranks/{rank_id}")
def admin_delete_rank(rank_id: int, db: Session = Depends(get_db)):
    return service.delete_game_rank(db, rank_id)


# ROLE CRUD
@router.get("/games/{game_id}/roles", response_model=list[GameRoleResponse])
def admin_list_roles(game_id: int, db: Session = Depends(get_db)):
    return service.list_game_roles(db, game_id)


@router.post("/games/{game_id}/roles", response_model=GameRoleResponse, status_code=status.HTTP_201_CREATED)
def admin_create_role(game_id: int, data: GameRoleCreate, db: Session = Depends(get_db)):
    return service.create_game_role(db, game_id, data)


@router.put("/game-roles/{role_id}", response_model=GameRoleResponse)
def admin_update_role(role_id: int, data: GameRoleUpdate, db: Session = Depends(get_db)):
    return service.update_game_role(db, role_id, data)


@router.delete("/game-roles/{role_id}")
def admin_delete_role(role_id: int, db: Session = Depends(get_db)):
    return service.delete_game_role(db, role_id)
