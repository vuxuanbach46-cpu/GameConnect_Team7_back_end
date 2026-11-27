from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.team import Team, TeamJoinMode
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.game import Game
from app.models.team_join_request import (
    TeamJoinRequest,
    TeamJoinRequestStatus,
)


class TeamJoinError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)



def get_user_teams(db: Session, user_id: int):
    """Danh sách các đội cố định mà người dùng đang là thành viên hoặc đội trưởng."""
    rows = (
        db.query(Team, Game, TeamMember)
        .join(Game, Game.id == Team.main_game_id)
        .outerjoin(
            TeamMember,
            and_(TeamMember.team_id == Team.id, TeamMember.user_id == user_id),
        )
        .filter(or_(Team.captain_id == user_id, TeamMember.user_id == user_id))
        .order_by(Team.updated_at.desc(), Team.id.desc())
        .all()
    )

    result = []
    for team, game, member in rows:
        member_count = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
        captain_recorded = db.query(TeamMember.id).filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == team.captain_id,
        ).first() is not None
        if not captain_recorded:
            member_count += 1

        result.append({
            "id": team.id,
            "name": team.name,
            "logo_url": team.logo_url,
            "description": team.description,
            "game_id": team.main_game_id,
            "game_name": game.name,
            "game_image": game.image,
            "captain_id": team.captain_id,
            "is_captain": team.captain_id == user_id,
            "member_role": "CAPTAIN" if team.captain_id == user_id else (member.role.value if member else "MEMBER"),
            "member_count": member_count,
            "max_members": team.max_members,
            "join_mode": team.join_mode.value,
            "joined_at": (member.joined_at if member else team.created_at),
        })
    return result

def join_team(
    db: Session,
    team_id: int,
    user_id: int,
    message: str | None = None,
):
    try:
        # 1. Kiểm tra đội và khóa bản ghi đội
        team = db.query(Team).filter(Team.id == team_id).with_for_update().first()

        if not team:
            raise TeamJoinError(404, "Đội không tồn tại")

        # Đội trưởng được tính là thành viên kể cả khi thiếu dòng team_members cũ.
        if team.captain_id == user_id:
            raise TeamJoinError(409, "Bạn đã là thành viên của đội này")

        # 2. Kiểm tra người dùng đã là thành viên chưa
        member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
            .first()
        )

        if member:
            raise TeamJoinError(409, "Bạn đã là thành viên của đội này")

        # 3. Kiểm tra số lượng thành viên
        members_query = db.query(TeamMember).filter(TeamMember.team_id == team_id)
        member_count = members_query.count()
        captain_is_recorded_as_member = (
            members_query.filter(TeamMember.user_id == team.captain_id).first()
            is not None
        )
        if not captain_is_recorded_as_member:
            member_count += 1

        if member_count >= team.max_members:
            raise TeamJoinError(409, "Đội đã đủ số lượng thành viên")

        # 4. Tìm yêu cầu tham gia cũ
        join_request = (
            db.query(TeamJoinRequest)
            .filter(
                TeamJoinRequest.team_id == team_id,
                TeamJoinRequest.user_id == user_id,
            )
            .with_for_update()
            .first()
        )

        # Membership is the source of truth. A previous request can remain
        # ACCEPTED after a captain removes that member; allow the user to join
        # again, directly for PUBLIC clubs or by reopening the request below.

        # 5. Nếu đội công khai thì tham gia trực tiếp
        if team.join_mode == TeamJoinMode.PUBLIC:

            db.add(
                TeamMember(
                    team_id=team_id,
                    user_id=user_id,
                    role=TeamMemberRole.MEMBER,
                )
            )

            if join_request:
                join_request.status = TeamJoinRequestStatus.ACCEPTED

            db.commit()

            return {
                "message": "Tham gia đội thành công",
                "status": "JOINED",
                "request_id": None,
            }

        # 6. Đội cần phê duyệt: kiểm tra yêu cầu trùng
        if join_request and join_request.status == TeamJoinRequestStatus.PENDING:
            raise TeamJoinError(409, "Bạn đã gửi yêu cầu tham gia đội này")

        # 7. Tạo mới hoặc cập nhật yêu cầu cũ
        if join_request:
            join_request.message = message
            join_request.status = TeamJoinRequestStatus.PENDING
        else:
            join_request = TeamJoinRequest(
                team_id=team_id,
                user_id=user_id,
                message=message,
                status=TeamJoinRequestStatus.PENDING,
            )
            db.add(join_request)

        db.commit()
        db.refresh(join_request)

        return {
            "message": "Gửi yêu cầu tham gia thành công, vui lòng chờ phê duyệt",
            "status": "PENDING",
            "request_id": join_request.id,
        }

    except TeamJoinError:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise TeamJoinError(409, "Yêu cầu tham gia không hợp lệ hoặc đã tồn tại")

    except Exception:
        db.rollback()
        raise


def cancel_join_request(
    db: Session,
    team_id: int,
    user_id: int,
):
    try:
        if not db.query(Team).filter(Team.id == team_id).first():
            raise TeamJoinError(404, "Đội không tồn tại")

        join_request = (
            db.query(TeamJoinRequest)
            .filter(
                TeamJoinRequest.team_id == team_id,
                TeamJoinRequest.user_id == user_id,
            )
            .with_for_update()
            .first()
        )

        if not join_request:
            raise TeamJoinError(404, "Không tìm thấy yêu cầu tham gia đội")

        if join_request.status != TeamJoinRequestStatus.PENDING:
            raise TeamJoinError(409, "Chỉ có thể hủy yêu cầu đang chờ phê duyệt")

        join_request.status = TeamJoinRequestStatus.CANCELLED

        db.commit()

        return {
            "message": "Hủy yêu cầu tham gia thành công",
            "status": "CANCELLED",
        }

    except TeamJoinError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


def get_my_join_request(
    db: Session,
    team_id: int,
    user_id: int,
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise TeamJoinError(404, "Đội không tồn tại")

    join_request = (
        db.query(TeamJoinRequest)
        .filter(
            TeamJoinRequest.team_id == team_id,
            TeamJoinRequest.user_id == user_id,
        )
        .first()
    )

    if not join_request:
        return {
            "exists": False,
            "request_id": None,
            "team_id": team_id,
            "status": None,
            "message": None,
            "created_at": None,
        }

    return {
        "exists": True,
        "request_id": join_request.id,
        "team_id": join_request.team_id,
        "status": join_request.status.value,
        "message": join_request.message,
        "created_at": join_request.created_at,
    }
