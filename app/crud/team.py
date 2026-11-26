from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException

from app.models.team import Team, TeamJoinMode
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.team_join_request import TeamJoinRequest, TeamJoinRequestStatus
from app.models.team_chat_message import TeamChatMessage
from app.models.team_feed_post import TeamFeedPost
from app.models.team_invitation import TeamInvitation
from app.models.user import User, UserRole
from app.models.game import Game

from app.schemas.team import (
    TeamCreateRequest,
    TeamUpdateRequest,
    JoinRequestStatusAction,
    TransferCaptainRequest,
    TeamResponse,
)
from app.crud.notification import create_notification
from sqlalchemy.exc import IntegrityError
from sqlalchemy import case
from sqlalchemy import delete


# Tạo đội
def create_team_service(info: TeamCreateRequest, db: Session, current_user: User):
    # 1. Kiểm tra tên đội
    team_name = " ".join(info.name.split())

    if not team_name:
        raise HTTPException(status_code=400, detail="Tên đội không được để trống")

    if len(team_name) < 2 or len(team_name) > 100:
        raise HTTPException(
            status_code=400, detail="Tên đội phải có từ 2 đến 100 ký tự"
        )

    # 2. Kiểm tra tên đội đã tồn tại
    existing_team = (
        db.query(Team).filter(func.lower(Team.name) == team_name.lower()).first()
    )

    if existing_team:
        raise HTTPException(
            status_code=409, detail="Tên đội đã tồn tại. Vui lòng chọn tên khác"
        )

    # 3. Kiểm tra game
    game = db.query(Game).filter(Game.id == info.main_game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game không tồn tại")

    if info.max_members > 100:
        raise HTTPException(
            status_code=400, detail="Số thành viên tối đa không được vượt quá 100"
        )

    # 5. Kiểm tra chế độ tham gia
    try:
        join_mode = TeamJoinMode(info.join_mode.value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Chế độ tham gia đội không hợp lệ")

    # 6. Chuẩn hóa logo và mô tả
    logo_url = info.logo_url.strip() if info.logo_url else None
    cover_url = info.cover_url.strip() if info.cover_url else None

    description = (
        info.description.strip()
        if info.description and info.description.strip()
        else None
    )

    # 7. Tạo đội và đội trưởng trong cùng transaction
    try:
        team = Team(
            name=team_name,
            logo_url=logo_url,
            cover_url=cover_url,
            main_game_id=info.main_game_id,
            description=description,
            captain_id=current_user.id,
            max_members=info.max_members,
            join_mode=join_mode,
        )

        db.add(team)
        db.flush()

        captain = TeamMember(
            team_id=team.id, user_id=current_user.id, role=TeamMemberRole.CAPTAIN
        )

        db.add(captain)

        db.commit()
        db.refresh(team)

        return team

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Tên đội đã tồn tại hoặc dữ liệu vi phạm ràng buộc database",
        )

    except Exception:
        db.rollback()
        raise


# Cập nhật thông tin đội
def update_team_service(
    team_id: int, info: TeamUpdateRequest, db: Session, current_user: User
):
    # 1. Kiểm tra đội tồn tại
    team = db.query(Team).filter(Team.id == team_id).with_for_update().first()

    if not team:
        raise HTTPException(status_code=404, detail="Đội không tồn tại")

    # 2. Kiểm tra quyền đội trưởng
    if team.captain_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Chỉ đội trưởng hoặc quản trị viên mới có quyền sửa thông tin đội",
        )

    # 3. Lấy dữ liệu cần cập nhật
    update_data = info.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Không có dữ liệu cần cập nhật")

    # 4. Không cho phép cập nhật các trường bắt buộc thành NULL
    required_fields = ["name", "main_game_id", "max_members", "join_mode"]

    for field in required_fields:
        if field in update_data and update_data[field] is None:
            raise HTTPException(status_code=400, detail=f"{field} không được để trống")

    # 5. Kiểm tra và chuẩn hóa tên đội
    if "name" in update_data:
        team_name = " ".join(update_data["name"].split())

        if len(team_name) < 2 or len(team_name) > 100:
            raise HTTPException(
                status_code=400, detail="Tên đội phải có từ 2 đến 100 ký tự"
            )

        # Kiểm tra trùng tên, loại trừ chính đội đang cập nhật
        existing_team = (
            db.query(Team)
            .filter(func.lower(Team.name) == team_name.lower(), Team.id != team_id)
            .first()
        )

        if existing_team:
            raise HTTPException(
                status_code=409, detail="Tên đội đã tồn tại. Vui lòng chọn tên khác"
            )

        update_data["name"] = team_name

    # 6. Kiểm tra game
    if "main_game_id" in update_data:
        game = db.query(Game).filter(Game.id == update_data["main_game_id"]).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game không tồn tại")

    # 7. Kiểm tra số thành viên tối đa
    if "max_members" in update_data:
        max_members = update_data["max_members"]

        if max_members < 2 or max_members > 100:
            raise HTTPException(
                status_code=400, detail="Số thành viên tối đa phải từ 2 đến 100"
            )

        current_members = (
            db.query(func.count(TeamMember.id))
            .filter(TeamMember.team_id == team_id)
            .scalar()
            or 0
        )

        if max_members < current_members:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Đội hiện có {current_members} thành viên. "
                    f"Không thể giảm giới hạn xuống {max_members}"
                ),
            )

    # 8. Kiểm tra chế độ tham gia
    if "join_mode" in update_data:
        try:
            update_data["join_mode"] = TeamJoinMode(update_data["join_mode"].value)
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="Chế độ tham gia không hợp lệ")

    # 9. Chuẩn hóa logo
    if "logo_url" in update_data:
        logo_url = update_data["logo_url"]

        if logo_url is not None:
            logo_url = logo_url.strip()

            if not logo_url:
                logo_url = None

        update_data["logo_url"] = logo_url

    if "cover_url" in update_data:
        cover_url = update_data["cover_url"]
        if cover_url is not None:
            cover_url = cover_url.strip() or None
        update_data["cover_url"] = cover_url

    # 10. Chuẩn hóa mô tả
    if "description" in update_data:
        description = update_data["description"]

        if description is not None:
            description = description.strip()

            if not description:
                description = None

        update_data["description"] = description

    # 11. Cập nhật database
    try:
        for key, value in update_data.items():
            setattr(team, key, value)

        db.commit()
        db.refresh(team)

        return team

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Dữ liệu cập nhật bị trùng hoặc vi phạm ràng buộc database",
        )

    except Exception:
        db.rollback()
        raise


# Tìm kiếm và phân trang
def get_teams_service(
    db: Session,
    keyword: str = None,
    game_id: int = None,
    join_mode: TeamJoinMode | None = None,
    page: int = 1,
    page_size: int = 10,
):
    # 1. Kiểm tra phân trang
    if page < 1:
        raise HTTPException(status_code=400, detail="Số trang phải lớn hơn hoặc bằng 1")

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400, detail="Số lượng đội mỗi trang phải từ 1 đến 100"
        )

    # 2. Chuẩn hóa từ khóa tìm kiếm
    if keyword is not None:
        keyword = keyword.strip()

        if len(keyword) > 100:
            raise HTTPException(
                status_code=400, detail="Từ khóa tìm kiếm không được vượt quá 100 ký tự"
            )

    # 3. Kiểm tra game nếu có lọc
    if game_id is not None:
        if game_id <= 0:
            raise HTTPException(status_code=400, detail="Game ID không hợp lệ")

        game = db.query(Game).filter(Game.id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game không tồn tại")

    if join_mode is not None and not isinstance(join_mode, TeamJoinMode):
        try:
            join_mode = TeamJoinMode(join_mode)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Chế độ tham gia không hợp lệ") from exc

    # 4. Khởi tạo truy vấn
    query = db.query(Team)

    # 5. Tìm kiếm theo tên đội
    if keyword:
        query = query.filter(Team.name.ilike(f"%{keyword}%", escape="\\"))

    # 6. Lọc theo game
    if game_id is not None:
        query = query.filter(Team.main_game_id == game_id)

    if join_mode is not None:
        query = query.filter(Team.join_mode == join_mode)

    # 7. Đếm tổng số đội thỏa mãn điều kiện
    total = query.count()

    # 8. Tính tổng số trang
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # 9. Lấy danh sách đội theo trang
    member_counts = (
        db.query(TeamMember.team_id.label("team_id"), func.count(TeamMember.id).label("member_count"))
        .group_by(TeamMember.team_id)
        .subquery()
    )
    captain_counts = (
        db.query(TeamMember.team_id.label("team_id"), func.count(TeamMember.id).label("captain_count"))
        .join(Team, and_(Team.id == TeamMember.team_id, Team.captain_id == TeamMember.user_id))
        .group_by(TeamMember.team_id)
        .subquery()
    )
    rows = (
        query.with_entities(
            Team,
            Game.name.label("game_name"),
            func.coalesce(member_counts.c.member_count, 0).label("member_count"),
            func.coalesce(captain_counts.c.captain_count, 0).label("captain_count"),
        )
        .join(Game, Game.id == Team.main_game_id)
        .outerjoin(member_counts, member_counts.c.team_id == Team.id)
        .outerjoin(captain_counts, captain_counts.c.team_id == Team.id)
        .order_by(Team.created_at.desc(), Team.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for team, game_name, member_count, captain_count in rows:
        item = TeamResponse.model_validate(team).model_dump(mode="json")
        item["game_name"] = game_name
        item["member_count"] = int(member_count or 0) + (0 if captain_count else 1)
        items.append(item)

    # 10. Trả kết quả
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# Chi tiết đội và danh sách thành viên
def get_team_detail_service(team_id: int, db: Session):
    # 1. Kiểm tra team_id
    if team_id <= 0:
        raise HTTPException(status_code=400, detail="Team ID không hợp lệ")

    # 2. Tìm đội
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Đội không tồn tại")

    # 3. Lấy danh sách thành viên và thông tin user
    members = (
        db.query(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .filter(TeamMember.team_id == team_id)
        .order_by(
            case((TeamMember.role == TeamMemberRole.CAPTAIN, 0), else_=1),
            TeamMember.joined_at.asc(),
            TeamMember.id.asc(),
        )
        .all()
    )

    # 4. Kiểm tra thành viên trùng lặp
    member_list = []
    seen_user_ids = set()

    for member, user in members:

        if user.id in seen_user_ids:
            continue

        seen_user_ids.add(user.id)

        member_list.append(
            {
                "user_id": user.id,
                "username": user.username,
                "role": member.role.value,
                "joined_at": member.joined_at,
            }
        )

    # 5. Kiểm tra đội trưởng có trong danh sách thành viên
    captain_exists = any(
        member["user_id"] == team.captain_id
        and member["role"] == TeamMemberRole.CAPTAIN.value
        for member in member_list
    )

    if not captain_exists:
        raise HTTPException(
            status_code=500,
            detail="Dữ liệu đội không hợp lệ: Không tìm thấy thành viên đội trưởng",
        )

    # 6. Kiểm tra số lượng thành viên
    total_members = len(member_list)

    if total_members > team.max_members:
        raise HTTPException(
            status_code=500,
            detail="Dữ liệu đội không hợp lệ: Số thành viên vượt giới hạn",
        )

    # 7. Trả kết quả
    return {
        "id": team.id,
        "name": team.name,
        "logo_url": team.logo_url,
        "cover_url": team.cover_url,
        "main_game_id": team.main_game_id,
        "description": team.description,
        "captain_id": team.captain_id,
        "max_members": team.max_members,
        "join_mode": team.join_mode.value,
        "total_members": total_members,
        "members": member_list,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
    }


# ==============================
# QUẢN LÝ THÀNH VIÊN & ĐƠN GIA NHẬP
# ==============================

# 1. Duyệt / Từ chối đơn xin gia nhập
def review_join_request_service(
    db: Session,
    team_id: int,
    request_id: int,
    status_action: JoinRequestStatusAction,
    current_user: User,
):
    team = db.query(Team).filter(Team.id == team_id).with_for_update().first()
    if not team:
        raise HTTPException(status_code=404, detail="Đội không tồn tại")

    if team.captain_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Chỉ đội trưởng câu lạc bộ mới có quyền duyệt đơn xin gia nhập",
        )
    if team.join_mode != TeamJoinMode.APPROVAL_REQUIRED:
        raise HTTPException(
            status_code=409,
            detail="Câu lạc bộ đang cho phép tham gia tự do, không thể duyệt yêu cầu gia nhập",
        )

    join_request = (
        db.query(TeamJoinRequest)
        .filter(
            TeamJoinRequest.id == request_id,
            TeamJoinRequest.team_id == team_id,
        )
        .with_for_update()
        .first()
    )
    if not join_request:
        raise HTTPException(
            status_code=404,
            detail="Đơn xin gia nhập không tồn tại hoặc không thuộc đội này",
        )

    if join_request.status != TeamJoinRequestStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Đơn xin gia nhập này đã được xử lý trước đó ({join_request.status.value})",
        )

    action_val = status_action.value if hasattr(status_action, "value") else str(status_action)

    if action_val == JoinRequestStatusAction.ACCEPTED.value:
        # Kiểm tra số lượng thành viên hiện tại
        current_members_count = (
            db.query(func.count(TeamMember.id))
            .filter(TeamMember.team_id == team_id)
            .scalar()
            or 0
        )
        captain_in_members = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == team.captain_id,
            )
            .first()
        )
        if not captain_in_members:
            current_members_count += 1

        if current_members_count >= team.max_members:
            raise HTTPException(
                status_code=409,
                detail=f"Đội đã đủ số lượng thành viên tối đa ({team.max_members})",
            )

        # Kiểm tra người dùng đã là thành viên chưa
        existing_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == join_request.user_id,
            )
            .first()
        )
        if existing_member or join_request.user_id == team.captain_id:
            join_request.status = TeamJoinRequestStatus.ACCEPTED
            db.commit()
            raise HTTPException(
                status_code=409,
                detail="Người dùng này đã là thành viên trong đội",
            )

        # Thêm thành viên mới
        new_member = TeamMember(
            team_id=team_id,
            user_id=join_request.user_id,
            role=TeamMemberRole.MEMBER,
        )
        db.add(new_member)
        join_request.status = TeamJoinRequestStatus.ACCEPTED

        # Tạo thông báo cho người được chấp nhận
        create_notification(
            db=db,
            recipient_id=join_request.user_id,
            type="TEAM_JOIN_ACCEPTED",
            content=f"Đơn xin gia nhập đội '{team.name}' của bạn đã được chấp nhận!",
            link=f"/teams/{team_id}",
        )

        db.commit()
        return {
            "request_id": join_request.id,
            "team_id": team_id,
            "user_id": join_request.user_id,
            "status": "ACCEPTED",
            "message": "Chấp nhận đơn xin gia nhập thành công",
        }

    else:
        # REJECTED
        join_request.status = TeamJoinRequestStatus.REJECTED

        create_notification(
            db=db,
            recipient_id=join_request.user_id,
            type="TEAM_JOIN_REJECTED",
            content=f"Đơn xin gia nhập đội '{team.name}' của bạn đã bị từ chối.",
            link=f"/teams/{team_id}",
        )

        db.commit()
        return {
            "request_id": join_request.id,
            "team_id": team_id,
            "user_id": join_request.user_id,
            "status": "REJECTED",
            "message": "Từ chối đơn xin gia nhập thành công",
        }


# 2. Xóa thành viên khỏi đội
def remove_team_member_service(
    db: Session,
    team_id: int,
    user_id: int,
    current_user: User,
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Đội trưởng không thể tự xóa chính mình khỏi đội. Vui lòng chuyển quyền đội trưởng trước",
        )

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Đội không tồn tại")

    if team.captain_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Chỉ đội trưởng mới có quyền xóa thành viên khỏi đội",
        )

    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Thành viên không tồn tại trong đội này",
        )

    db.delete(member)

    # Gửi thông báo cho thành viên bị xóa
    create_notification(
        db=db,
        recipient_id=user_id,
        type="TEAM_MEMBER_REMOVED",
        content=f"Bạn đã bị xóa khỏi đội '{team.name}'.",
        link=f"/teams/{team_id}",
    )

    db.commit()
    return {
        "team_id": team_id,
        "user_id": user_id,
        "message": f"Đã xóa thành viên khỏi đội '{team.name}' thành công",
    }


def delete_team_service(db: Session, team_id: int, current_user: User):
    """Delete a club and its associated membership, invitation, feed, and chat data."""
    team = db.query(Team).filter(Team.id == team_id).with_for_update().first()
    if not team:
        raise HTTPException(status_code=404, detail="Câu lạc bộ không tồn tại")
    if team.captain_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Chỉ đội trưởng câu lạc bộ mới có quyền xóa câu lạc bộ này",
        )

    team_name = team.name
    try:
        # Explicitly delete children so this works consistently across DB engines,
        # including databases where FK cascade is not enabled for every table.
        db.execute(delete(TeamChatMessage).where(TeamChatMessage.team_id == team_id))
        db.execute(delete(TeamFeedPost).where(TeamFeedPost.team_id == team_id))
        db.execute(delete(TeamInvitation).where(TeamInvitation.team_id == team_id))
        db.execute(delete(TeamJoinRequest).where(TeamJoinRequest.team_id == team_id))
        db.execute(delete(TeamMember).where(TeamMember.team_id == team_id))
        db.delete(team)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"team_id": team_id, "message": f"Đã xóa câu lạc bộ '{team_name}' thành công"}


# 3. Chuyển quyền Đội trưởng
def transfer_captain_service(
    db: Session,
    team_id: int,
    info: TransferCaptainRequest,
    current_user: User,
):
    new_captain_id = info.new_captain_id

    if new_captain_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Bạn hiện tại đã là đội trưởng của đội này",
        )

    team = db.query(Team).filter(Team.id == team_id).with_for_update().first()
    if not team:
        raise HTTPException(status_code=404, detail="Đội không tồn tại")

    if team.captain_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Chỉ đội trưởng hiện tại mới có quyền chuyển quyền đội trưởng",
        )

    # Kiểm tra thành viên mới có trong đội không
    new_captain_member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == new_captain_id,
        )
        .with_for_update()
        .first()
    )
    if not new_captain_member:
        raise HTTPException(
            status_code=400,
            detail="Thành viên được chỉ định không thuộc đội này",
        )

    try:
        old_captain_id = team.captain_id
        team.captain_id = new_captain_id

        # Đổi vai trò của đội trưởng cũ thành MEMBER
        old_captain_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == old_captain_id,
            )
            .with_for_update()
            .first()
        )
        if old_captain_member:
            old_captain_member.role = TeamMemberRole.MEMBER
        else:
            db.add(
                TeamMember(
                    team_id=team_id,
                    user_id=old_captain_id,
                    role=TeamMemberRole.MEMBER,
                )
            )

        # Đổi vai trò của thành viên mới thành CAPTAIN
        new_captain_member.role = TeamMemberRole.CAPTAIN

        # Tạo thông báo cho tân đội trưởng
        create_notification(
            db=db,
            recipient_id=new_captain_id,
            type="TEAM_CAPTAIN_TRANSFERRED",
            content=f"Bạn đã được chỉ định làm Đội trưởng mới của đội '{team.name}'.",
            link=f"/teams/{team_id}",
        )

        db.commit()
        db.refresh(team)

        return {
            "team_id": team.id,
            "team_name": team.name,
            "old_captain_id": old_captain_id,
            "new_captain_id": new_captain_id,
            "message": f"Chuyển quyền đội trưởng cho thành viên {new_captain_id} thành công",
        }
    except Exception:
        db.rollback()
        raise


# 4. Thành viên tự rời đội
def leave_team_service(
    db: Session,
    team_id: int,
    current_user: User,
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Đội không tồn tại")

    # Ràng buộc: Đội trưởng không thể tự rời đội
    if team.captain_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Đội trưởng không thể tự rời đội. Vui lòng chuyển quyền đội trưởng cho thành viên khác trước khi rời đội",
        )

    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Bạn không phải là thành viên của đội này",
        )

    try:
        db.delete(member)

        # Tạo thông báo cho Đội trưởng
        create_notification(
            db=db,
            recipient_id=team.captain_id,
            type="TEAM_MEMBER_LEFT",
            content=f"Thành viên '{current_user.username}' đã tự rời khỏi đội '{team.name}'.",
            link=f"/teams/{team_id}",
        )

        db.commit()
        return {
            "team_id": team_id,
            "user_id": current_user.id,
            "message": f"Bạn đã rời khỏi đội '{team.name}' thành công",
        }
    except Exception:
        db.rollback()
        raise
