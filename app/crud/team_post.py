"""CRUD cho TeamPost, TeamPostRole, TeamPostApplication.

Bao gồm đầy đủ các quy tắc nghiệp vụ (Business Rules) và validation:
- Validate game theo danh mục game
- Validate rank tối thiểu / tối đa theo game
- Validate vai trò theo game
- Validate số người cần 1–9 người
- Validate hạn hiển thị tối đa 7 ngày
- Mỗi user tối đa 3 bài đăng đang mở (OPEN)
"""
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.models.user_game import UserGame
from app.models.team_post import (
    ApplicationStatus,
    PostStatus,
    TeamPost,
    TeamPostApplication,
    TeamPostRole,
)
from app.crud.notification import create_notification
from app.schemas.team_post import (
    TeamPostApplicationCreate,
    TeamPostApplicationUpdate,
    TeamPostCreate,
    TeamPostUpdate,
)


# ---------------------------------------------------------------------------
# TeamPost CRUD
# ---------------------------------------------------------------------------

def get_team_posts(
    db: Session,
    game_id: int | None = None,
    rank_id: int | None = None,
    min_rank_id: int | None = None,
    max_rank_id: int | None = None,
    role_id: int | None = None,
    play_time: str | None = None,
    region: str | None = None,
    q: str | None = None,
    status_filter: PostStatus | None = PostStatus.OPEN,
    include_expired: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[TeamPost], int]:
    """Danh sách và tìm kiếm bài đăng.

    Quy tắc:
    - Tìm theo game_id
    - Tìm theo rank_id (phù hợp khoảng min_rank - max_rank của bài)
    - Tìm theo vai trò (role_id)
    - Tìm theo giờ chơi (play_time substring)
    - Tìm theo khu vực (region substring)
    - Tìm theo từ khóa (q: tiêu đề hoặc mô tả)
    - Mặc định chỉ lấy bài OPEN và còn hạn (expires_at is NULL hoặc expires_at > now())
    - Sắp xếp mới nhất (created_at DESC)
    - Phân trang (page, page_size)
    """
    query = select(TeamPost)

    # 1. Lọc theo game
    if game_id:
        query = query.where(TeamPost.game_id == game_id)

    # 2. Lọc theo rank người chơi (nằm trong khoảng min_rank -> max_rank của bài)
    if rank_id:
        target_rank = db.get(GameRank, rank_id)
        if target_rank:
            min_rank_subq = (
                select(GameRank.rank_order)
                .where(GameRank.id == TeamPost.min_rank_id)
                .scalar_subquery()
            )
            max_rank_subq = (
                select(GameRank.rank_order)
                .where(GameRank.id == TeamPost.max_rank_id)
                .scalar_subquery()
            )
            query = query.where(
                or_(TeamPost.min_rank_id.is_(None), min_rank_subq <= target_rank.rank_order),
                or_(TeamPost.max_rank_id.is_(None), max_rank_subq >= target_rank.rank_order),
            )
        else:
            query = query.where(
                or_(TeamPost.min_rank_id == rank_id, TeamPost.max_rank_id == rank_id)
            )

    if min_rank_id:
        query = query.where(TeamPost.min_rank_id == min_rank_id)
    if max_rank_id:
        query = query.where(TeamPost.max_rank_id == max_rank_id)

    # 3. Lọc theo vai trò (role_id)
    if role_id:
        query = query.where(
            TeamPost.id.in_(
                select(TeamPostRole.team_post_id).where(TeamPostRole.game_role_id == role_id)
            )
        )

    # 4. Lọc theo giờ chơi
    if play_time:
        query = query.where(TeamPost.play_time.ilike(f"%{play_time.strip()}%"))

    # 5. Lọc theo khu vực
    if region:
        query = query.where(TeamPost.region.ilike(f"%{region.strip()}%"))

    # 6. Tìm kiếm từ khóa (q: tiêu đề hoặc mô tả)
    if q:
        kw = f"%{q.strip()}%"
        query = query.where(or_(TeamPost.title.ilike(kw), TeamPost.description.ilike(kw)))

    # 7. Trạng thái (mặc định chỉ OPEN)
    if status_filter:
        query = query.where(TeamPost.status == status_filter)

    # 8. Hạn hiển thị: chỉ bài còn hạn (mặc định)
    if not include_expired:
        now = datetime.now()
        query = query.where(
            or_(TeamPost.expires_at.is_(None), TeamPost.expires_at > now)
        )

    # Đếm tổng số bài khớp điều kiện
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total = db.scalar(count_query) or 0

    # 9. Sắp xếp mới nhất
    query = query.order_by(TeamPost.created_at.desc())

    # 10. Phân trang
    offset = max(0, (page - 1) * page_size)
    items = list(db.scalars(query.offset(offset).limit(page_size)).unique())

    return items, total


def get_recommended_team_posts(
    db: Session,
    user_id: int | None = None,
    limit: int = 6,
) -> tuple[list[TeamPost], bool, list[str]]:
    """Gợi ý bài đăng tìm đội phù hợp theo game và rank trong hồ sơ người chơi (T3CCE98).

    Quy tắc nghiệp vụ:
    1. Lấy danh sách game và rank trong hồ sơ của người dùng (user_games).
    2. Nếu người dùng có cấu hình game trong hồ sơ:
       - Với mỗi game/rank của user:
         + game_id khớp với game của bài đăng (TeamPost.game_id == ug.game_id).
         + Rank của user phải nằm trong khoảng [min_rank, max_rank] của bài:
           * min_rank_id IS NULL hoặc min_rank.rank_order <= user_rank.rank_order
           * max_rank_id IS NULL hoặc max_rank.rank_order >= user_rank.rank_order
         + Nếu bài đăng không yêu cầu rank (min & max đều NULL) thì phù hợp mọi rank.
       - Bài đăng phải OPEN, chưa hết hạn, và không phải do chính user đăng (TeamPost.user_id != user_id).
       - Ưu tiên các bài đăng khớp tiêu chí, sắp xếp mới nhất (created_at DESC).
       - Nếu số lượng bài khớp ít hơn limit, bổ sung các bài đăng OPEN khác (đang tuyển sôi nổi) để giao diện luôn đầy đặn.
    3. Nếu người dùng chưa có game trong hồ sơ (hoặc chưa đăng nhập):
       - Trả về danh sách bài đăng OPEN mới nhất, đánh dấu has_profile_games = False.
    """
    now = datetime.now()
    user_games = []
    if user_id:
        user_games = db.query(UserGame).filter(UserGame.user_id == user_id).all()

    has_profile_games = len(user_games) > 0
    matched_labels: list[str] = []
    match_conditions = []
    game_rank_map: dict[int, str] = {}

    for ug in user_games:
        game_obj = db.get(Game, ug.game_id)
        game_name = game_obj.name if game_obj else f"Game #{ug.game_id}"

        if ug.rank_id:
            user_rank = db.get(GameRank, ug.rank_id)
            if user_rank:
                label = f"{game_name} ({user_rank.rank_name})"
                matched_labels.append(label)
                game_rank_map[ug.game_id] = f"Rank {user_rank.rank_name}"

                min_rank_subq = (
                    select(GameRank.rank_order)
                    .where(GameRank.id == TeamPost.min_rank_id)
                    .scalar_subquery()
                )
                max_rank_subq = (
                    select(GameRank.rank_order)
                    .where(GameRank.id == TeamPost.max_rank_id)
                    .scalar_subquery()
                )
                cond = and_(
                    TeamPost.game_id == ug.game_id,
                    or_(TeamPost.min_rank_id.is_(None), min_rank_subq <= user_rank.rank_order),
                    or_(TeamPost.max_rank_id.is_(None), max_rank_subq >= user_rank.rank_order),
                )
                match_conditions.append(cond)
                continue

        matched_labels.append(game_name)
        game_rank_map[ug.game_id] = "Mọi rank"
        match_conditions.append(TeamPost.game_id == ug.game_id)

    # Base filter: bài phải OPEN và chưa hết hạn
    base_filter = [
        TeamPost.status == PostStatus.OPEN,
        or_(TeamPost.expires_at.is_(None), TeamPost.expires_at > now),
    ]
    if user_id:
        base_filter.append(TeamPost.user_id != user_id)

    recommended_posts: list[TeamPost] = []

    if match_conditions:
        matched_query = (
            select(TeamPost)
            .where(*base_filter, or_(*match_conditions))
            .order_by(TeamPost.created_at.desc())
            .limit(limit)
        )
        matched_list = list(db.scalars(matched_query).unique())
        for post in matched_list:
            reason = game_rank_map.get(post.game_id, "Khớp game hồ sơ")
            setattr(post, "match_reason", f"Phù hợp: {reason}")
        recommended_posts.extend(matched_list)

    # Bổ sung bài nếu chưa đủ limit
    if len(recommended_posts) < limit:
        already_ids = [p.id for p in recommended_posts]
        backfill_filter = list(base_filter)
        if already_ids:
            backfill_filter.append(~TeamPost.id.in_(already_ids))

        needed = limit - len(recommended_posts)
        backfill_query = (
            select(TeamPost)
            .where(*backfill_filter)
            .order_by(TeamPost.created_at.desc())
            .limit(needed)
        )
        backfill_list = list(db.scalars(backfill_query).unique())
        for post in backfill_list:
            setattr(post, "match_reason", "Đang tuyển sôi nổi")
        recommended_posts.extend(backfill_list)

    return recommended_posts, has_profile_games, matched_labels


def get_team_post(db: Session, post_id: int) -> TeamPost | None:
    return db.get(TeamPost, post_id)


def create_team_post(
    db: Session,
    data: TeamPostCreate,
    user_id: int,
) -> TeamPost:
    """Tạo bài đăng tìm đội kèm đầy đủ business validation."""
    # 1. Kiểm tra giới hạn: Mỗi user tối đa 3 bài đang mở (PostStatus.OPEN)
    open_posts_count = (
        db.query(TeamPost)
        .filter(TeamPost.user_id == user_id, TeamPost.status == PostStatus.OPEN)
        .count()
    )
    if open_posts_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mỗi người dùng chỉ được có tối đa 3 bài đăng tìm đội đang mở (OPEN)",
        )

    # 2. Validate game theo danh mục game
    game = db.get(Game, data.game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trò chơi (game_id={data.game_id}) không tồn tại trong hệ thống",
        )

    # 3. Validate rank theo danh mục game
    min_rank = None
    max_rank = None
    if data.min_rank_id is not None:
        min_rank = db.get(GameRank, data.min_rank_id)
        if not min_rank:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối thiểu (id={data.min_rank_id}) không tồn tại",
            )
        if min_rank.game_id != data.game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối thiểu '{min_rank.rank_name}' không thuộc game '{game.name}'",
            )

    if data.max_rank_id is not None:
        max_rank = db.get(GameRank, data.max_rank_id)
        if not max_rank:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối đa (id={data.max_rank_id}) không tồn tại",
            )
        if max_rank.game_id != data.game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối đa '{max_rank.rank_name}' không thuộc game '{game.name}'",
            )

    if min_rank and max_rank and min_rank.rank_order > max_rank.rank_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rank tối thiểu ({min_rank.rank_name}) không được cao hơn rank tối đa ({max_rank.rank_name})",
        )

    # 4. Validate vai trò (role_ids) theo danh mục game
    unique_role_ids = list(dict.fromkeys(data.role_ids))
    for r_id in unique_role_ids:
        role = db.get(GameRole, r_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vai trò (id={r_id}) không tồn tại",
            )
        if role.game_id != data.game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vai trò '{role.role_name}' không thuộc game '{game.name}'",
            )

    # 5. Validate số người cần 1–9 người
    if data.needed_players < 1 or data.needed_players > 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số lượng thành viên cần tuyển phải từ 1 đến 9 người",
        )

    # 6. Validate hạn hiển thị tối đa 7 ngày
    now = datetime.now()
    max_expiry = now + timedelta(days=7)

    if data.expires_at is None:
        expires_at = max_expiry
    else:
        user_expiry = (
            data.expires_at.replace(tzinfo=None)
            if data.expires_at.tzinfo
            else data.expires_at
        )
        if user_expiry <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hạn hiển thị bài đăng phải lớn hơn thời điểm hiện tại",
            )
        if user_expiry > max_expiry + timedelta(minutes=5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hạn hiển thị bài đăng tối đa không được vượt quá 7 ngày kể từ hiện tại",
            )
        expires_at = user_expiry

    # 7. Lưu bài đăng
    try:
        post = TeamPost(
            user_id=user_id,
            game_id=data.game_id,
            title=data.title,
            min_rank_id=data.min_rank_id,
            max_rank_id=data.max_rank_id,
            needed_players=data.needed_players,
            play_time=data.play_time,
            region=data.region,
            description=data.description,
            status=PostStatus.OPEN,
            expires_at=expires_at,
        )
        db.add(post)
        db.flush()

        for r_id in unique_role_ids:
            role = TeamPostRole(
                team_post_id=post.id,
                game_id=post.game_id,
                game_role_id=r_id,
            )
            db.add(role)

        db.commit()
        db.refresh(post)
        return post
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi lưu bài đăng: {str(exc)}",
        )


def update_team_post(db: Session, post: TeamPost, data: TeamPostUpdate) -> TeamPost:
    """Cập nhật bài đăng tìm đội kèm đầy đủ validation."""
    if data.needed_players is not None and (data.needed_players < 1 or data.needed_players > 9):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số lượng thành viên cần tuyển phải từ 1 đến 9 người",
        )

    if data.expires_at is not None:
        now = datetime.now()
        max_expiry = now + timedelta(days=7)
        user_expiry = (
            data.expires_at.replace(tzinfo=None)
            if data.expires_at.tzinfo
            else data.expires_at
        )
        if user_expiry <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hạn hiển thị bài đăng phải lớn hơn thời điểm hiện tại",
            )
        if user_expiry > max_expiry + timedelta(minutes=5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hạn hiển thị bài đăng tối đa không được vượt quá 7 ngày kể từ hiện tại",
            )

    # Validate rank nếu có cập nhật
    eff_min_id = data.min_rank_id if data.min_rank_id is not None else post.min_rank_id
    eff_max_id = data.max_rank_id if data.max_rank_id is not None else post.max_rank_id

    min_rank_obj = None
    max_rank_obj = None

    if data.min_rank_id is not None:
        min_rank_obj = db.get(GameRank, data.min_rank_id)
        if not min_rank_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối thiểu (id={data.min_rank_id}) không tồn tại",
            )
        if min_rank_obj.game_id != post.game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rank tối thiểu không thuộc trò chơi của bài đăng này",
            )

    if data.max_rank_id is not None:
        max_rank_obj = db.get(GameRank, data.max_rank_id)
        if not max_rank_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối đa (id={data.max_rank_id}) không tồn tại",
            )
        if max_rank_obj.game_id != post.game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rank tối đa không thuộc trò chơi của bài đăng này",
            )

    if eff_min_id and eff_max_id:
        min_r = min_rank_obj or db.get(GameRank, eff_min_id)
        max_r = max_rank_obj or db.get(GameRank, eff_max_id)
        if min_r and max_r and min_r.rank_order > max_r.rank_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối thiểu ({min_r.rank_name}) không được cao hơn rank tối đa ({max_r.rank_name})",
            )

    update_data = data.model_dump(exclude_unset=True, exclude={"role_ids", "user_id"})
    for field, value in update_data.items():
        setattr(post, field, value)

    # Nếu gửi role_ids → ghi đè toàn bộ danh sách vai trò
    if data.role_ids is not None:
        unique_role_ids = list(dict.fromkeys(data.role_ids))
        for r_id in unique_role_ids:
            role = db.get(GameRole, r_id)
            if not role or role.game_id != post.game_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Vai trò (id={r_id}) không thuộc trò chơi của bài đăng này",
                )
        db.execute(delete(TeamPostRole).where(TeamPostRole.team_post_id == post.id))
        for role_id in unique_role_ids:
            role = TeamPostRole(
                team_post_id=post.id,
                game_id=post.game_id,
                game_role_id=role_id,
            )
            db.add(role)

    try:
        db.commit()
        db.refresh(post)
        return post
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi cập nhật bài đăng: {str(exc)}",
        )


def close_team_post(db: Session, post: TeamPost) -> TeamPost:
    """Đóng bài đăng tìm đội sớm (status -> CLOSED)."""
    post.status = PostStatus.CLOSED
    try:
        db.commit()
        db.refresh(post)
        return post
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi cập nhật bài đăng: {str(exc)}",
        )


def delete_team_post(db: Session, post: TeamPost) -> None:
    """Xóa bài đăng tìm đội (cascade roles và applications)."""
    db.delete(post)
    db.commit()


# ---------------------------------------------------------------------------
# TeamPostApplication CRUD
# ---------------------------------------------------------------------------

def get_applications_by_post(db: Session, post_id: int) -> list[TeamPostApplication]:
    query = (
        select(TeamPostApplication)
        .where(TeamPostApplication.team_post_id == post_id)
        .order_by(TeamPostApplication.created_at.asc())
    )
    return list(db.scalars(query))


def get_application(db: Session, application_id: int) -> TeamPostApplication | None:
    return db.get(TeamPostApplication, application_id)


def create_application(
    db: Session, team_post_id: int, user_id: int, data: TeamPostApplicationCreate
) -> TeamPostApplication:
    # 1. Kiểm tra bài đăng tồn tại
    post = db.get(TeamPost, team_post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Bài đăng không tồn tại")

    # 2. Kiểm tra bài đăng có đang OPEN không
    if post.status != PostStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bài đăng không còn mở nhận ứng tuyển",
        )

    # 3. Kiểm tra bài đăng đã hết hạn chưa
    now = datetime.now()
    if post.expires_at and post.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bài đăng đã hết hạn ứng tuyển",
        )

    # 4. Không ứng tuyển bài của chính mình
    if post.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể tự ứng tuyển vào bài đăng của chính mình",
        )

    # 5. Kiểm tra ứng tuyển trùng lặp
    existing_app = (
        db.query(TeamPostApplication)
        .filter(
            TeamPostApplication.team_post_id == team_post_id,
            TeamPostApplication.user_id == user_id,
        )
        .first()
    )
    if existing_app:
        if existing_app.status in (ApplicationStatus.PENDING, ApplicationStatus.ACCEPTED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn đã gửi đơn ứng tuyển vào bài đăng này rồi",
            )
        # Nếu trước đó đã CANCELLED hoặc REJECTED thì cho phép ứng tuyển lại (cập nhật lại PENDING)
        existing_app.status = ApplicationStatus.PENDING
        existing_app.message = data.message
        app = existing_app
    else:
        app = TeamPostApplication(
            team_post_id=team_post_id,
            user_id=user_id,
            message=data.message,
            status=ApplicationStatus.PENDING,
        )
        db.add(app)

    # 6. Gửi thông báo đến chủ bài đăng qua module Thông báo
    applicant_name = f"Người dùng #{user_id}"
    user_obj = db.get(User, user_id)
    if user_obj:
        applicant_name = user_obj.username or f"Người dùng #{user_id}"

    create_notification(
        db=db,
        recipient_id=post.user_id,
        type="TEAM_POST_APPLICATION",
        content=f"{applicant_name} đã gửi đơn ứng tuyển vào bài đăng '{post.title}'.",
        link=f"/pages/team-post-detail.html?id={post.id}",
    )

    db.commit()
    db.refresh(app)
    return app


def update_application_status(
    db: Session,
    application: TeamPostApplication,
    data: TeamPostApplicationUpdate,
    current_user: User,
) -> TeamPostApplication:
    """Cập nhật trạng thái đơn ứng tuyển:

    - Chủ bài / ADMIN: có quyền ACCEPTED hoặc REJECTED đơn ứng tuyển.
      + Khi ACCEPTED: nếu đủ số người cần tuyển (accepted_count >= needed_players),
        bài đăng tự động chuyển sang trạng thái FULL.
      + Gửi thông báo đến người ứng tuyển.
    - Người ứng tuyển: có quyền CANCELLED (rút đơn của mình).
      + Gửi thông báo đến chủ bài đăng.
      + Nếu đơn rút trước đó đã ACCEPTED và bài đăng đang FULL, kiểm tra mở lại OPEN.
    """
    post = application.post or db.get(TeamPost, application.team_post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Bài đăng không tồn tại")

    user_role = getattr(current_user, "role", None)
    role_str = getattr(user_role, "value", user_role)
    is_owner_or_admin = (current_user.id == post.user_id) or (role_str == "ADMIN")
    is_applicant = current_user.id == application.user_id

    if not is_owner_or_admin and not is_applicant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật đơn ứng tuyển này",
        )

    if is_owner_or_admin:
        if data.status not in (ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chủ bài đăng chỉ có thể chấp nhận (ACCEPTED) hoặc từ chối (REJECTED) đơn ứng tuyển",
            )

        if data.status == ApplicationStatus.ACCEPTED:
            if application.status == ApplicationStatus.ACCEPTED:
                return application

            if post.status == PostStatus.CLOSED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bài đăng đã đóng, không thể duyệt thêm đơn ứng tuyển",
                )

            # Đếm số người đã được duyệt ACCEPTED hiện tại
            accepted_count = (
                db.query(func.count(TeamPostApplication.id))
                .filter(
                    TeamPostApplication.team_post_id == post.id,
                    TeamPostApplication.status == ApplicationStatus.ACCEPTED,
                )
                .scalar()
                or 0
            )

            if accepted_count >= post.needed_players:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bài đăng đã tuyển đủ số người (đã đạt giới hạn)",
                )

            application.status = ApplicationStatus.ACCEPTED

            # Khi đủ người thì bài chuyển FULL
            if accepted_count + 1 >= post.needed_players:
                post.status = PostStatus.FULL

            # Gửi thông báo đến người ứng tuyển
            create_notification(
                db=db,
                recipient_id=application.user_id,
                type="TEAM_POST_APPLICATION_ACCEPTED",
                content=f"Đơn ứng tuyển của bạn vào bài đăng '{post.title}' đã được chấp nhận!",
                link=f"/pages/team-post-detail.html?id={post.id}",
            )

        elif data.status == ApplicationStatus.REJECTED:
            prev_status = application.status
            application.status = ApplicationStatus.REJECTED

            # Nếu trước đó đã ACCEPTED và bài đăng đang FULL, mở lại OPEN nếu còn thiếu người
            if prev_status == ApplicationStatus.ACCEPTED and post.status == PostStatus.FULL:
                other_accepted = (
                    db.query(func.count(TeamPostApplication.id))
                    .filter(
                        TeamPostApplication.team_post_id == post.id,
                        TeamPostApplication.id != application.id,
                        TeamPostApplication.status == ApplicationStatus.ACCEPTED,
                    )
                    .scalar()
                    or 0
                )
                if other_accepted < post.needed_players:
                    post.status = PostStatus.OPEN

            # Gửi thông báo từ chối đến người ứng tuyển
            create_notification(
                db=db,
                recipient_id=application.user_id,
                type="TEAM_POST_APPLICATION_REJECTED",
                content=f"Đơn ứng tuyển của bạn vào bài đăng '{post.title}' đã bị từ chối.",
                link=f"/pages/team-post-detail.html?id={post.id}",
            )

    else:
        # Người ứng tuyển tự rút đơn
        if data.status != ApplicationStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Người ứng tuyển chỉ được phép rút đơn (CANCELLED)",
            )

        prev_status = application.status
        application.status = ApplicationStatus.CANCELLED

        # Nếu trước đó đã ACCEPTED và bài đăng đang FULL, mở lại OPEN nếu còn thiếu người
        if prev_status == ApplicationStatus.ACCEPTED and post.status == PostStatus.FULL:
            other_accepted = (
                db.query(func.count(TeamPostApplication.id))
                .filter(
                    TeamPostApplication.team_post_id == post.id,
                    TeamPostApplication.id != application.id,
                    TeamPostApplication.status == ApplicationStatus.ACCEPTED,
                )
                .scalar()
                or 0
            )
            if other_accepted < post.needed_players:
                post.status = PostStatus.OPEN

        applicant_name = f"Người dùng #{application.user_id}"
        user_obj = db.get(User, application.user_id)
        if user_obj:
            applicant_name = user_obj.username or f"Người dùng #{application.user_id}"

        # Gửi thông báo đến chủ bài đăng
        create_notification(
            db=db,
            recipient_id=post.user_id,
            type="TEAM_POST_APPLICATION_CANCELLED",
            content=f"{applicant_name} đã rút đơn ứng tuyển khỏi bài đăng '{post.title}'.",
            link=f"/pages/team-post-detail.html?id={post.id}",
        )

    db.commit()
    db.refresh(application)
    return application


def delete_application(db: Session, application: TeamPostApplication) -> None:
    post = application.post or db.get(TeamPost, application.team_post_id)
    prev_status = application.status
    db.delete(application)
    db.flush()
    if post and prev_status == ApplicationStatus.ACCEPTED and post.status == PostStatus.FULL:
        accepted_count = (
            db.query(func.count(TeamPostApplication.id))
            .filter(
                TeamPostApplication.team_post_id == post.id,
                TeamPostApplication.status == ApplicationStatus.ACCEPTED,
            )
            .scalar()
            or 0
        )
        if accepted_count < post.needed_players:
            post.status = PostStatus.OPEN
    db.commit()
