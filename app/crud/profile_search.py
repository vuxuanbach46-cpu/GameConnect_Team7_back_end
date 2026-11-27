from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.models.gamer_profile import GamerProfile
from app.models.user import User, UserStatus
from app.models.user_game import UserGame


def _validate_filters(
    db: Session,
    game_id: int | None,
    rank_id: int | None,
    role_id: int | None,
) -> None:
    """Kiểm tra ID bộ lọc và bảo đảm rank/role thuộc cùng một game."""
    selected_game_id = game_id

    if game_id is not None and db.query(Game.id).filter(Game.id == game_id).first() is None:
        raise HTTPException(status_code=404, detail="Game không tồn tại")

    rank = None
    if rank_id is not None:
        rank = db.query(GameRank).filter(GameRank.id == rank_id).first()
        if rank is None:
            raise HTTPException(status_code=404, detail="Rank không tồn tại")
        if selected_game_id is not None and rank.game_id != selected_game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rank không thuộc game đã chọn",
            )
        selected_game_id = selected_game_id or rank.game_id

    role = None
    if role_id is not None:
        role = db.query(GameRole).filter(GameRole.id == role_id).first()
        if role is None:
            raise HTTPException(status_code=404, detail="Vai trò không tồn tại")
        if selected_game_id is not None and role.game_id != selected_game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vai trò và rank/game phải thuộc cùng một game",
            )


def search_gamer_profiles(
    db: Session,
    *,
    q: str | None = None,
    game_id: int | None = None,
    rank_id: int | None = None,
    role_id: int | None = None,
    region: str | None = None,
    play_time: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Tìm hồ sơ công khai và phân trang; các điều kiện game dùng cùng một UserGame."""
    _validate_filters(db, game_id, rank_id, role_id)

    query = (
        db.query(GamerProfile, User.username)
        .join(User, GamerProfile.user_id == User.id)
        .filter(
            GamerProfile.is_public.is_(True),
            User.status == UserStatus.ACTIVE,
        )
    )

    if q and q.strip():
        keyword = f"%{q.strip()}%"
        query = query.filter(
            or_(
                GamerProfile.display_name.ilike(keyword),
                User.username.ilike(keyword),
            )
        )

    if region and region.strip():
        query = query.filter(GamerProfile.region.ilike(f"%{region.strip()}%"))

    if play_time and play_time.strip():
        query = query.filter(GamerProfile.play_time.ilike(f"%{play_time.strip()}%"))

    # Dùng EXISTS để không nhân bản hồ sơ khi người chơi có nhiều game.
    # Nếu đồng thời lọc game/rank/role, tất cả phải khớp trên cùng bản ghi user_games.
    if game_id is not None or rank_id is not None or role_id is not None:
        game_filter = db.query(UserGame.id).filter(
            UserGame.user_id == GamerProfile.user_id
        )

        if game_id is not None:
            game_filter = game_filter.filter(UserGame.game_id == game_id)

        if rank_id is not None:
            game_filter = game_filter.join(
                GameRank, GameRank.id == UserGame.rank_id
            ).filter(
                GameRank.id == rank_id,
                GameRank.game_id == UserGame.game_id,
            )

        if role_id is not None:
            game_filter = game_filter.join(
                GameRole, GameRole.id == UserGame.role_id
            ).filter(
                GameRole.id == role_id,
                GameRole.game_id == UserGame.game_id,
            )

        query = query.filter(game_filter.exists())

    total = query.order_by(None).count()
    rows = (
        query.order_by(GamerProfile.updated_at.desc(), GamerProfile.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    user_ids = [profile.user_id for profile, _username in rows]
    games_by_user: dict[int, list[dict]] = {user_id: [] for user_id in user_ids}

    if user_ids:
        user_games = (
            db.query(UserGame)
            .options(
                joinedload(UserGame.game),
                joinedload(UserGame.rank),
                joinedload(UserGame.role),
            )
            .filter(UserGame.user_id.in_(user_ids))
            .order_by(UserGame.created_at.asc(), UserGame.id.asc())
            .all()
        )

        for user_game in user_games:
            game = user_game.game
            if game is None:
                continue

            games_by_user.setdefault(user_game.user_id, []).append(
                {
                    "id": game.id,
                    "name": game.name,
                    "image": game.image,
                    "genre": game.genre,
                    "rank": (
                        {
                            "id": user_game.rank.id,
                            "rank_name": user_game.rank.rank_name,
                            "rank_order": user_game.rank.rank_order,
                        }
                        if user_game.rank is not None
                        else None
                    ),
                    "role": (
                        {
                            "id": user_game.role.id,
                            "role_name": user_game.role.role_name,
                        }
                        if user_game.role is not None
                        else None
                    ),
                    "in_game_id": user_game.in_game_id,
                }
            )

    items = []
    for profile, username in rows:
        items.append(
            {
                "id": profile.id,
                "user_id": profile.user_id,
                "username": username,
                "display_name": profile.display_name,
                "avatar": profile.avatar,
                "bio": profile.bio,
                "region": profile.region,
                "play_time": profile.play_time,
                "has_mic": profile.has_mic,
                "games": games_by_user.get(profile.user_id, []),
            }
        )

    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": ceil(total / page_size) if total else 0,
        },
    }
