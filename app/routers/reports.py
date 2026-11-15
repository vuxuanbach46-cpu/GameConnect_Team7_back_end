from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.crud.report import create_report
from app.db.session import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.report import Report
from app.models.team_post import TeamPost
from app.models.user import User
from app.schemas.api_response import api_repoint
from app.schemas.report import ReportCreate, ReportTargetType

router = APIRouter(prefix="/reports", tags=["Reports"])

TARGET_MODELS = {
    ReportTargetType.USER: User,
    ReportTargetType.POST: Post,
    ReportTargetType.COMMENT: Comment,
    ReportTargetType.TEAM_POST: TeamPost,
}


def report_data(report: Report):
    return {
        "id": report.id,
        "reporter_id": report.reporter_id,
        "target_type": report.target_type,
        "target_id": report.target_id,
        "reason": report.reason,
        "description": report.description,
        "status": report.status,
        "created_at": report.created_at,
    }


@router.post("", summary="Báo cáo tài khoản, bài viết, bình luận hoặc bài tìm đội")
def submit_report(
    req: Request,
    info: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_model = TARGET_MODELS[info.target_type]
    target = db.query(target_model).filter(target_model.id == info.target_id).first()

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Đối tượng cần báo cáo không tồn tại",
        )

    if info.target_type == ReportTargetType.USER and info.target_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể báo cáo chính tài khoản của mình",
        )

    existed = db.query(Report).filter(
        Report.reporter_id == current_user.id,
        Report.target_type == info.target_type.value,
        Report.target_id == info.target_id,
    ).first()
    if existed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bạn đã báo cáo đối tượng này rồi",
        )

    try:
        report = create_report(
            db=db,
            reporter_id=current_user.id,
            target_type=info.target_type.value,
            target_id=info.target_id,
            reason=info.reason.value,
            description=info.description,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bạn đã báo cáo đối tượng này rồi",
        )

    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Gửi báo cáo thành công",
        data=report_data(report),
    )
