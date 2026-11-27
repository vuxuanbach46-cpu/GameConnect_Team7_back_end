from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user

from app.crud import team_join as crud

from app.schemas.team_join import (
    JoinTeamRequest,
)

from app.schemas.api_response import api_repoint
from app.models.user import User

router = APIRouter(
    prefix="/teams",
    tags=["Team Join"],
)

@router.get("/me", summary="Danh sách đội tôi đang tham gia")
def get_my_teams(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    teams = crud.get_user_teams(db=db, user_id=current_user.id)
    return api_repoint(
        req=req,
        status_code=200,
        message="Danh sách đội đang tham gia",
        data=teams,
    )

# Gửi yêu cầu hoặc tham gia đội
@router.post(
    "/{team_id}/join",
    summary="Gửi yêu cầu tham gia đội hoặc tham gia trực tiếp nếu đội cho phép",
    description="Gửi yêu cầu tham gia đội hoặc tham gia trực tiếp nếu đội cho phép. Nếu đội ở chế độ 'OPEN', người dùng sẽ được thêm vào đội ngay lập tức. Nếu đội ở chế độ 'REQUEST', người dùng sẽ gửi yêu cầu tham gia và chờ quản lý đội chấp nhận.",
)
def join_team(
    team_id: Annotated[int, Path(ge=1)],
    req: Request,
    data: JoinTeamRequest | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = crud.join_team(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
        message=data.message if data else None,
    )

    return api_repoint(
        req=req,
        status_code=200,
        message=result["message"],
        data={
            "status": result["status"],
            "request_id": result["request_id"],
        },
    )


# Hủy yêu cầu tham gia
@router.delete(
    "/{team_id}/join-request",
    summary="Hủy yêu cầu tham gia đội",
    description="Hủy yêu cầu tham gia đội đang chờ xử lý.",
)
def cancel_join_request(
    team_id: Annotated[int, Path(ge=1)],
    req: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = crud.cancel_join_request(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
    )

    return api_repoint(
        req=req,
        status_code=200,
        message=result["message"],
        data={
            "status": result["status"],
        },
    )


# Xem trạng thái yêu cầu tham gia
@router.get(
    "/{team_id}/join-request/me",
    summary="Xem trạng thái yêu cầu tham gia đội",
    description="Xem trạng thái yêu cầu tham gia đội đang chờ xử lý.",
)
def get_my_join_request(
    team_id: Annotated[int, Path(ge=1)],
    req: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = crud.get_my_join_request(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
    )

    return api_repoint(
        req=req,
        status_code=200,
        message="Lấy trạng thái yêu cầu tham gia thành công",
        data=result,
    )
