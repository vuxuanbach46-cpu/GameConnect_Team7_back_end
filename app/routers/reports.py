from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.crud.notification import create_notification
from app.crud.report import create_report
from app.crud.user import lock_user_account
from app.db.session import get_db
from app.models.comment import Comment
from app.models.notification import Notification
from app.models.post import Post
from app.models.report import Report
from app.models.team_post import TeamPost
from app.models.user import User
from app.schemas.api_response import api_repoint
from app.schemas.report import (
    ModerationAction,
    PostVisibilityUpdate,
    ReportCreate,
    ReportResolve,
    ReportStatus,
    ReportTargetType,
    ReportCreate,
)

public_router = APIRouter(prefix="/reports", tags=["Reports"])

TARGET_MODELS = {
    ReportTargetType.USER: User,
    ReportTargetType.POST: Post,
    ReportTargetType.COMMENT: Comment,
    ReportTargetType.TEAM_POST: TeamPost,
}

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin - Content Moderation"],
    dependencies=[Depends(get_current_user), Depends(require_admin)],
)


def report_data(report: Report, reporter: User | None = None):
    return {
        "id": report.id,
        "reporter_id": report.reporter_id,
        "reporter_username": reporter.username if reporter else None,
        "target_type": report.target_type,
        "target_id": report.target_id,
        "reason": report.reason,
        "description": report.description,
        "status": report.status,
        "handler_id": report.handler_id,
        "result": report.result,
        "created_at": report.created_at,
        "handled_at": report.handled_at,
    }


@router.get("/reports", summary="Danh sách báo cáo")
def admin_list_reports(
    req: Request,
    report_status: ReportStatus | None = Query(default=None, alias="status"),
    target_type: ReportTargetType | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Report, User).join(User, User.id == Report.reporter_id)

    if report_status:
        query = query.filter(Report.status == report_status.value)

    if target_type:
        query = query.filter(Report.target_type == target_type.value)

    total = query.count()
    rows = (
        query.order_by(Report.created_at.desc(), Report.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy danh sách báo cáo thành công",
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [report_data(report, reporter) for report, reporter in rows],
        },
    )


def apply_moderation_action(
    db: Session,
    action: ModerationAction,
    target_type: str,
    target_id: int,
    admin_id: int,
):
    if action in (ModerationAction.HIDE_POST, ModerationAction.SHOW_POST):
        if target_type != ReportTargetType.POST.value:
            raise HTTPException(status_code=400, detail="Thao tác này chỉ áp dụng cho bài viết")

        post = db.query(Post).filter(Post.id == target_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại")

        post.status = (
            "HIDDEN" if action == ModerationAction.HIDE_POST else "VISIBLE"
        )

    elif action == ModerationAction.DELETE_COMMENT:
        if target_type != ReportTargetType.COMMENT.value:
            raise HTTPException(status_code=400, detail="Thao tác này chỉ áp dụng cho bình luận")

        comment = db.query(Comment).filter(Comment.id == target_id).first()
        if comment is None:
            raise HTTPException(status_code=404, detail="Bình luận không tồn tại")

        db.delete(comment)

    elif action == ModerationAction.LOCK_USER:
        if target_type != ReportTargetType.USER.value:
            raise HTTPException(status_code=400, detail="Thao tác này chỉ áp dụng cho tài khoản")

        if target_id == admin_id:
            raise HTTPException(status_code=400, detail="Không thể khóa tài khoản của chính mình")

        lock_user_account(db, target_id)


@router.patch("/reports/{report_id}/resolve", summary="Xử lý báo cáo")
def resolve_report(
    report_id: int,
    info: ReportResolve,
    req: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()

    if report is None:
        raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")

    if report.status != "PENDING":
        raise HTTPException(status_code=409, detail="Báo cáo này đã được xử lý")

    if info.action and info.status != ReportStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Không thể thực hiện thao tác khi từ chối báo cáo")

    try:
        if info.action:
            apply_moderation_action(
                db=db,
                action=info.action,
                target_type=report.target_type,
                target_id=report.target_id,
                admin_id=admin.id,
            )

        report.status = info.status.value
        report.handler_id = admin.id
        report.result = info.result.strip()
        report.handled_at = datetime.now()

        create_notification(
            db=db,
            recipient_id=report.reporter_id,
            type="REPORT_RESULT",
            content=f"Báo cáo của bạn đã được xử lý: {info.result.strip()}"[:500],
            link=None,
        )

        db.commit()
        db.refresh(report)

    except Exception:
        db.rollback()
        raise

    reporter = db.query(User).filter(User.id == report.reporter_id).first()

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Xử lý báo cáo thành công",
        data=report_data(report, reporter),
    )


@router.patch("/posts/{post_id}/visibility", summary="Ẩn hoặc hiện bài viết")
def update_post_visibility(
    post_id: int,
    info: PostVisibilityUpdate,
    req: Request,
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Bài viết không tồn tại")

    post.status = info.status
    db.commit()
    db.refresh(post)

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Cập nhật trạng thái bài viết thành công",
        data={"id": post.id, "status": post.status},
    )


@router.delete("/comments/{comment_id}", summary="Xóa bình luận vi phạm")
def delete_comment(
    comment_id: int,
    req: Request,
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if comment is None:
        raise HTTPException(status_code=404, detail="Bình luận không tồn tại")

    db.delete(comment)
    db.commit()

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Xóa bình luận thành công",
        data={"id": comment_id},
    )


@router.patch("/users/{user_id}/lock", summary="Khóa tài khoản vi phạm")
def lock_user(
    user_id: int,
    req: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Không thể khóa tài khoản của chính mình")

    user = lock_user_account(db, user_id)
    db.commit()

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Khóa tài khoản thành công",
        data={"id": user.id, "status": user.status},
    )
