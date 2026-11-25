from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.schemas.game import GameCatalogResponse

router = APIRouter(prefix="/api/games", tags=["Games Catalog"])

DEFAULT_GAMES_CATALOG = [
    {
        "name": "Valorant",
        "genre": "FPS",
        "aliases": {"valorant"},
        "ranks": [
            "Iron 1", "Iron 2", "Iron 3",
            "Bronze 1", "Bronze 2", "Bronze 3",
            "Silver 1", "Silver 2", "Silver 3",
            "Gold 1", "Gold 2", "Gold 3",
            "Platinum 1", "Platinum 2", "Platinum 3",
            "Diamond 1", "Diamond 2", "Diamond 3",
            "Ascendant 1", "Ascendant 2", "Ascendant 3",
            "Immortal 1", "Immortal 2", "Immortal 3",
            "Radiant",
        ],
        "roles": ["Duelist", "Initiator", "Controller", "Sentinel"],
    },
    {
        "name": "Counter-Strike 2",
        "genre": "FPS",
        "aliases": {"counter-strike 2", "cs2", "counter strike 2", "cs:go", "csgo"},
        "ranks": [
            "FACEIT Level 1", "FACEIT Level 2", "FACEIT Level 3",
            "FACEIT Level 4", "FACEIT Level 5", "FACEIT Level 6",
            "FACEIT Level 7", "FACEIT Level 8", "FACEIT Level 9",
            "FACEIT Level 10", "FACEIT Challenger",
        ],
        "roles": ["AWPer", "Entry", "IGL", "Support", "Lurker"],
    },
    {
        "name": "Liên Quân Mobile",
        "genre": "MOBA",
        "aliases": {"liên quân mobile", "lien quan mobile", "liên quân", "aov", "arena of valor"},
        "ranks": [
            "Đồng", "Bạc", "Vàng", "Bạch Kim", "Kim Cương",
            "Tinh Anh", "Cao Thủ", "Chiến Tướng", "Thách Đấu",
        ],
        "roles": ["Top", "Jungle", "Mid", "ADC", "Support"],
    },
    {
        "name": "Liên Minh Huyền Thoại",
        "genre": "MOBA",
        "aliases": {"liên minh huyền thoại", "lien minh huyen thoai", "lmht", "lol", "league of legends"},
        "ranks": [
            "Sắt", "Đồng", "Bạc", "Vàng", "Bạch Kim", "Lục Bảo",
            "Kim Cương", "Cao Thủ", "Đại Cao Thủ", "Thách Đấu",
        ],
        "roles": ["Top", "Jungle", "Mid", "ADC", "Support"],
    },
    {
        "name": "Đấu Trường Chân Lý",
        "genre": "Strategy",
        "aliases": {"đấu trường chân lý", "dau truong chan ly", "dtcl", "đtcl", "tft", "teamfight tactics"},
        "ranks": [
            "Sắt", "Đồng", "Bạc", "Vàng", "Bạch Kim", "Lục Bảo",
            "Kim Cương", "Cao Thủ", "Đại Cao Thủ", "Thách Đấu",
        ],
        "roles": ["Reroll", "Fast 8", "Fast 9", "Flex"],
    },
]


def ensure_default_games_seeded(db: Session) -> None:
    """Đảm bảo đủ 5 tựa game chuẩn kèm Ranks và Roles trong Database mà không tạo trùng lặp."""
    try:
        existing_games = (
            db.query(Game)
            .options(joinedload(Game.ranks), joinedload(Game.roles))
            .all()
        )
        changed = False

        for spec in DEFAULT_GAMES_CATALOG:
            aliases = spec["aliases"]
            matched_game = None
            for g in existing_games:
                if g.name and g.name.strip().lower() in aliases:
                    matched_game = g
                    break

            if matched_game is None:
                matched_game = Game(
                    name=spec["name"],
                    genre=spec["genre"],
                    image=None,
                )
                db.add(matched_game)
                db.flush()
                existing_games.append(matched_game)
                changed = True

            existing_rank_names = {
                r.rank_name.strip().lower()
                for r in (matched_game.ranks or [])
                if r.rank_name
            }
            if not existing_rank_names:
                for idx, r_name in enumerate(spec["ranks"], start=1):
                    db.add(
                        GameRank(
                            game_id=matched_game.id,
                            rank_name=r_name,
                            rank_order=idx,
                        )
                    )
                changed = True

            existing_role_names = {
                ro.role_name.strip().lower()
                for ro in (matched_game.roles or [])
                if ro.role_name
            }
            if not existing_role_names:
                for ro_name in spec["roles"]:
                    db.add(
                        GameRole(
                            game_id=matched_game.id,
                            role_name=ro_name,
                        )
                    )
                changed = True

        if changed:
            db.commit()
    except Exception:
        db.rollback()


@router.get("", response_model=list[GameCatalogResponse])
def get_games_catalog(db: Session = Depends(get_db)):
    """Danh mục game để frontend hiển thị lựa chọn game, rank và role."""
    ensure_default_games_seeded(db)
    return (
        db.query(Game)
        .options(joinedload(Game.ranks), joinedload(Game.roles))
        .order_by(Game.id.asc())
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
