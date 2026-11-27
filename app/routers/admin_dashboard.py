from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.db.session import get_db
from app.models.game import Game
from app.models.post import Post
from app.models.report import Report
from app.models.team import Team
from app.models.team_post import PostStatus as TeamPostStatus, TeamPost
from app.models.user import User, UserStatus
from app.schemas.api_response import api_repoint


router = APIRouter(
    prefix="/api/admin/dashboard",
    tags=["Admin - Dashboard & Statistics"],
    dependencies=[Depends(get_current_user), Depends(require_admin)],
)


@router.get("/stats", summary="Thống kê tổng quan Admin Dashboard")
def get_dashboard_stats(
    request: Request,
    days: int = Query(default=14, ge=7, le=90, description="Số ngày thống kê người dùng mới"),
    db: Session = Depends(get_db),
):
    now = datetime.now()
    start_date = (now - timedelta(days=days - 1)).date()

    # 1. TỔNG QUAN CÁC CHỈ SỐ (SUMMARY METRICS)
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == UserStatus.ACTIVE).count()
    locked_users = db.query(User).filter(User.status == UserStatus.LOCKED).count()

    total_teams = db.query(Team).count()

    total_team_posts = db.query(TeamPost).count()
    open_team_posts = db.query(TeamPost).filter(TeamPost.status == TeamPostStatus.OPEN).count()

    total_posts = db.query(Post).count()
    visible_posts = db.query(Post).filter(Post.status == "VISIBLE").count()

    pending_reports = db.query(Report).filter(Report.status == "PENDING").count()
    resolved_reports = db.query(Report).filter(Report.status == "RESOLVED").count()
    rejected_reports = db.query(Report).filter(Report.status == "REJECTED").count()
    total_reports = db.query(Report).count()

    # 2. NGƯỜI DÙNG MỚI THEO NGÀY (CHO BIỂU ĐỒ CHART.JS)
    user_daily_rows = (
        db.query(func.date(User.created_at).label("d"), func.count(User.id).label("c"))
        .filter(func.date(User.created_at) >= start_date)
        .group_by(func.date(User.created_at))
        .all()
    )
    user_daily_dict = {row.d: row.c for row in user_daily_rows}

    user_growth = []
    for i in range(days):
        current_d = start_date + timedelta(days=i)
        user_growth.append({
            "date": current_d.strftime("%Y-%m-%d"),
            "label": current_d.strftime("%d/%m"),
            "count": int(user_daily_dict.get(current_d, 0)),
        })

    # 3. BÀI ĐĂNG TÌM ĐỘI THEO TỪNG GAME (GAME DISTRIBUTION)
    team_posts_by_game_rows = (
        db.query(Game.name, func.count(TeamPost.id))
        .join(Game, Game.id == TeamPost.game_id)
        .group_by(Game.name)
        .all()
    )
    team_posts_by_game = [
        {"game": row[0], "count": int(row[1])} for row in team_posts_by_game_rows
    ]

    # 4. BÁO CÁO THEO LOẠI ĐỐI TƯỢNG (REPORT TARGETS)
    report_type_rows = (
        db.query(Report.target_type, func.count(Report.id))
        .group_by(Report.target_type)
        .all()
    )
    reports_by_type = {row[0]: int(row[1]) for row in report_type_rows}

    # 5. DANH SÁCH BÁO CÁO CHỜ XỬ LÝ GẦN NHẤT (RECENT PENDING REPORTS)
    recent_reports_query = (
        db.query(Report, User.username.label("reporter_username"))
        .outerjoin(User, User.id == Report.reporter_id)
        .filter(Report.status == "PENDING")
        .order_by(Report.created_at.desc(), Report.id.desc())
        .limit(5)
        .all()
    )
    recent_pending_reports = [
        {
            "id": r.id,
            "reporter_username": uname or f"ID {r.reporter_id}",
            "target_type": r.target_type,
            "target_id": r.target_id,
            "reason": r.reason,
            "description": r.description,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r, uname in recent_reports_query
    ]

    # 6. DANH SÁCH NGƯỜI DÙNG MỚI THAM GIA GẦN ĐÂY (RECENT USERS)
    recent_users_query = (
        db.query(User)
        .order_by(User.created_at.desc(), User.id.desc())
        .limit(5)
        .all()
    )
    recent_users = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "status": u.status.value if hasattr(u.status, "value") else str(u.status),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in recent_users_query
    ]

    data = {
        "summary": {
            "total_users": total_users,
            "active_users": active_users,
            "locked_users": locked_users,
            "total_teams": total_teams,
            "total_team_posts": total_team_posts,
            "open_team_posts": open_team_posts,
            "total_posts": total_posts,
            "visible_posts": visible_posts,
            "pending_reports": pending_reports,
            "resolved_reports": resolved_reports,
            "rejected_reports": rejected_reports,
            "total_reports": total_reports,
        },
        "user_growth": user_growth,
        "team_posts_by_game": team_posts_by_game,
        "reports_by_type": reports_by_type,
        "recent_pending_reports": recent_pending_reports,
        "recent_users": recent_users,
    }

    return api_repoint(
        req=request,
        status_code=status.HTTP_200_OK,
        message="Lấy thống kê Admin Dashboard thành công",
        data=data,
    )
