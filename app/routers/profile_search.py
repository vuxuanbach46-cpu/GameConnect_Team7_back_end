from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_optional_user
from app.crud.profile_search import search_gamer_profiles
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile_search import GamerProfileSearchResponse

router = APIRouter(prefix="/api/profiles", tags=["Gamer Profile Search"])


@router.get("/search", response_model=GamerProfileSearchResponse)
def search_profiles(
    q: str | None = Query(default=None, max_length=100, description="Tìm theo tên hiển thị hoặc username"),
    game_id: int | None = Query(default=None, gt=0, description="ID game"),
    rank_id: int | None = Query(default=None, gt=0, description="ID rank"),
    role_id: int | None = Query(default=None, gt=0, description="ID vai trò"),
    region: str | None = Query(default=None, max_length=100, description="Tìm khu vực, không phân biệt hoa thường"),
    play_time: str | None = Query(default=None, max_length=100, description="Tìm khung giờ chơi, không phân biệt hoa thường"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User | None = Depends(get_optional_user),
):
    """Tìm kiếm hồ sơ game thủ công khai với bộ lọc và phân trang."""
    return search_gamer_profiles(
        db,
        q=q,
        game_id=game_id,
        rank_id=rank_id,
        role_id=role_id,
        region=region,
        play_time=play_time,
        page=page,
        page_size=page_size,
    )
