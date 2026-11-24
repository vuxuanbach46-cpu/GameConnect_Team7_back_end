from fastapi import APIRouter, Depends, Request, HTTPException, Query, status

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.game import Game

from app.db.session import get_db
from app.core.security import get_current_user, get_optional_user

from app.schemas.team import (
    TeamCreateRequest,
    TeamUpdateRequest,
    ReviewJoinRequest,
    TransferCaptainRequest,
)

from app.models.user import User
from app.schemas.api_response import api_repoint, APIRepoint

from app.crud.team import (
    create_team_service,
    update_team_service,
    get_teams_service,
    get_team_detail_service,
    review_join_request_service,
    remove_team_member_service,
    transfer_captain_service,
    leave_team_service,
)

router = APIRouter(prefix="/teams", tags=["Teams"])


# ==============================
# COMMON RESPONSE
# ==============================


def success_response(req: Request, status_code: int, message: str, data=None):
    return api_repoint(
        req=req, status_code=status_code, message=message, data=jsonable_encoder(data)
    )


def error_response(req: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            api_repoint(
                req=req,
                status_code=exc.status_code,
                message=str(exc.detail),
                error=exc.detail,
            )
        ),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=APIRepoint,
    summary="Tạo đội",
    description="Tạo đội mới",
)
def create_team(
    req: Request,
    info: TeamCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        team = create_team_service(info=info, db=db, current_user=current_user)

        return success_response(
            req=req, status_code=201, message="Tạo đội thành công", data=team
        )

    except HTTPException as exc:
        return error_response(req, exc)


@router.put(
    "/{team_id}",
    response_model=APIRepoint,
    summary="Cập nhật đội",
    description="Cập nhật thông tin đội",
)
def update_team(
    req: Request,
    team_id: int,
    info: TeamUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        team = update_team_service(
            team_id=team_id, info=info, db=db, current_user=current_user
        )

        return success_response(
            req=req, status_code=200, message="Cập nhật đội thành công", data=team
        )

    except HTTPException as exc:
        return error_response(req, exc)


@router.get(
    "",
    response_model=APIRepoint,
    dependencies=[Depends(get_optional_user)],
    summary="Lấy danh sách đội",
    description="Lấy danh sách đội theo từ khóa và game_id (nếu có)",
)
def get_teams(
    req: Request,
    keyword: str = Query(default=None, max_length=100),
    game_id: int = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        result = get_teams_service(
            db=db, keyword=keyword, game_id=game_id, page=page, page_size=page_size
        )

        return success_response(
            req=req,
            status_code=200,
            message="Lấy danh sách đội thành công",
            data=result,
        )

    except HTTPException as exc:
        return error_response(req, exc)


@router.get("/mine", response_model=APIRepoint, summary="Danh sách đội của người đăng nhập")
def get_my_teams(req: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member_counts = (db.query(TeamMember.team_id, func.count(TeamMember.user_id).label("count"))
                     .group_by(TeamMember.team_id).subquery())
    membership = db.query(TeamMember.team_id).filter(TeamMember.user_id == current_user.id)
    rows = (db.query(Team, Game.name, member_counts.c.count)
            .join(Game, Game.id == Team.main_game_id)
            .outerjoin(member_counts, member_counts.c.team_id == Team.id)
            .filter(or_(Team.captain_id == current_user.id, Team.id.in_(membership)))
            .order_by(Team.name, Team.id).all())
    data = [{"id": team.id, "name": team.name, "game": game, "description": team.description,
             "role": "captain" if team.captain_id == current_user.id else "member",
             "members": count or 0, "maxMembers": team.max_members}
            for team, game, count in rows]
    return success_response(req, 200, "Lấy danh sách đội thành công", data)


@router.get(
    "/{team_id}",
    response_model=APIRepoint,
    dependencies=[Depends(get_optional_user)],
    summary="Lấy thông tin chi tiết đội",
    description="Lấy thông tin chi tiết đội theo team_id",
)
def get_team_detail(
    req: Request,
    team_id: int,
    db: Session = Depends(get_db),
):
    try:
        result = get_team_detail_service(team_id=team_id, db=db)

        return success_response(
            req=req,
            status_code=200,
            message="Lấy thông tin đội thành công",
            data=result,
        )

    except HTTPException as exc:
        return error_response(req, exc)


# ==============================
# 1. DUYỆT / TỪ CHỐI ĐƠN XIN GIA NHẬP
# ==============================
@router.patch(
    "/{team_id}/join-requests/{request_id}",
    response_model=APIRepoint,
    summary="Duyệt hoặc từ chối đơn xin gia nhập",
    description="Đội trưởng cập nhật trạng thái đơn (ACCEPTED hoặc REJECTED). Nếu chấp nhận, hệ thống kiểm tra giới hạn max_members, thêm user vào team_members và tạo thông báo.",
)
def review_join_request(
    req: Request,
    team_id: int,
    request_id: int,
    info: ReviewJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = review_join_request_service(
            db=db,
            team_id=team_id,
            request_id=request_id,
            status_action=info.status,
            current_user=current_user,
        )
        return success_response(
            req=req,
            status_code=200,
            message=result["message"],
            data=result,
        )
    except HTTPException as exc:
        return error_response(req, exc)


# ==============================
# 2. XÓA THÀNH VIÊN KHỎI ĐỘI
# ==============================
@router.delete(
    "/{team_id}/members/{user_id}",
    response_model=APIRepoint,
    summary="Xóa thành viên khỏi đội",
    description="Đội trưởng xóa một thành viên khỏi đội (không được xóa chính mình) và gửi thông báo.",
)
def remove_team_member(
    req: Request,
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = remove_team_member_service(
            db=db,
            team_id=team_id,
            user_id=user_id,
            current_user=current_user,
        )
        return success_response(
            req=req,
            status_code=200,
            message=result["message"],
            data=result,
        )
    except HTTPException as exc:
        return error_response(req, exc)


# ==============================
# 3. CHUYỂN QUYỀN ĐỘI TRƯỞNG
# ==============================
@router.patch(
    "/{team_id}/transfer-captain",
    response_model=APIRepoint,
    summary="Chuyển quyền Đội trưởng",
    description="Đội trưởng hiện tại nhường quyền cho một thành viên khác trong đội, cập nhật lại bảng teams (captain_id) và vai trò (role) trong team_members qua Transaction.",
)
def transfer_captain(
    req: Request,
    team_id: int,
    info: TransferCaptainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = transfer_captain_service(
            db=db,
            team_id=team_id,
            info=info,
            current_user=current_user,
        )
        return success_response(
            req=req,
            status_code=200,
            message=result["message"],
            data=result,
        )
    except HTTPException as exc:
        return error_response(req, exc)


# ==============================
# 4. THÀNH VIÊN TỰ RỜI ĐỘI
# ==============================
@router.post(
    "/{team_id}/leave",
    response_model=APIRepoint,
    summary="Thành viên tự rời đội",
    description="Thành viên tự thoát khỏi đội. Ràng buộc: Nếu người gọi là đội trưởng, hệ thống bắt buộc phải từ chối và yêu cầu chuyển quyền trước.",
)
def leave_team(
    req: Request,
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = leave_team_service(
            db=db,
            team_id=team_id,
            current_user=current_user,
        )
        return success_response(
            req=req,
            status_code=200,
            message=result["message"],
            data=result,
        )
    except HTTPException as exc:
        return error_response(req, exc)
