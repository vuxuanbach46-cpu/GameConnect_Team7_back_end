"""Unit tests verifying task T3CD622:
[Bonus] Tạo đội từ bài đăng đủ người
- Bài đăng chuyển FULL thì chủ bài bấm "Tạo đội" để tạo đội với các thành viên đã được chấp nhận.
- Kiểm tra quyền: chỉ chủ bài đăng mới được tạo.
- Kiểm tra số lượng: bài đăng chưa đủ người bị từ chối 400.
- Kiểm tra tạo Team, TeamMember (Captain + Members), notifications.
- Kiểm tra xử lý tự động chống trùng tên đội.
- Kiểm tra endpoint FastAPI POST /api/team-posts/{id}/create-team.
"""
import unittest
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.models.user import User, UserRole, UserStatus
from app.models.game import Game
from app.models.team import Team, TeamJoinMode
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.notification import Notification
from app.models.team_post import (
    ApplicationStatus,
    PostStatus,
    TeamPost,
    TeamPostApplication,
)
from app.schemas.team_post import CreateTeamFromPostRequest
from app.crud.team_post import create_team_from_full_post
from app.routers.team_post import router as team_post_router
from app.core.security import get_current_user

# Test in-memory SQLite database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine)


class TestCreateTeamFromPost(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = TestSession()
        # Clean DB
        self.db.query(Notification).delete()
        self.db.query(TeamMember).delete()
        self.db.query(Team).delete()
        self.db.query(TeamPostApplication).delete()
        self.db.query(TeamPost).delete()
        self.db.query(Game).delete()
        self.db.query(User).delete()
        self.db.commit()

        # Seed users
        self.owner = User(
            id=1,
            email="owner@test.com",
            username="captain_user",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        self.applicant1 = User(
            id=2,
            email="app1@test.com",
            username="member_one",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        self.applicant2 = User(
            id=3,
            email="app2@test.com",
            username="member_two",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        self.stranger = User(
            id=4,
            email="stranger@test.com",
            username="stranger_user",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        self.game = Game(id=1, name="League of Legends", genre="MOBA")
        self.db.add_all([self.owner, self.applicant1, self.applicant2, self.stranger, self.game])
        self.db.commit()

        # Seed full post (needed_players = 2, 2 accepted applicants)
        self.full_post = TeamPost(
            id=10,
            user_id=self.owner.id,
            game_id=self.game.id,
            title="Leo Rank Cao Thu 5v5",
            needed_players=2,
            play_time="20h-23h",
            region="VN",
            status=PostStatus.FULL,
            expires_at=datetime.utcnow() + timedelta(days=2),
        )
        self.db.add(self.full_post)
        self.db.commit()

        self.app1 = TeamPostApplication(
            id=101,
            team_post_id=self.full_post.id,
            user_id=self.applicant1.id,
            message="Xin 1 slot Mid",
            status=ApplicationStatus.ACCEPTED,
        )
        self.app2 = TeamPostApplication(
            id=102,
            team_post_id=self.full_post.id,
            user_id=self.applicant2.id,
            message="Xin 1 slot Jungle",
            status=ApplicationStatus.ACCEPTED,
        )
        self.db.add_all([self.app1, self.app2])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_create_team_from_full_post_success(self):
        """Chủ bài đăng tạo đội thành công khi bài đã FULL."""
        req = CreateTeamFromPostRequest(
            name="Team Chien Than",
            description="Doi hinh leo rank cao thu",
            join_mode="APPROVAL_REQUIRED",
        )
        result = create_team_from_full_post(
            db=self.db,
            post_id=self.full_post.id,
            current_user_id=self.owner.id,
            data=req,
        )

        self.assertEqual(result["team_name"], "Team Chien Than")
        self.assertEqual(result["captain_id"], self.owner.id)
        self.assertEqual(result["main_game_id"], self.game.id)
        self.assertEqual(result["members_count"], 3)  # Captain + 2 members

        # Kiểm tra Team trong DB
        team = self.db.get(Team, result["team_id"])
        self.assertIsNotNone(team)
        self.assertEqual(team.name, "Team Chien Than")
        self.assertEqual(team.captain_id, self.owner.id)

        # Kiểm tra TeamMember trong DB
        members = self.db.query(TeamMember).filter(TeamMember.team_id == team.id).all()
        self.assertEqual(len(members), 3)

        captain_m = next((m for m in members if m.user_id == self.owner.id), None)
        self.assertIsNotNone(captain_m)
        self.assertEqual(captain_m.role, TeamMemberRole.CAPTAIN)

        member_ids = {m.user_id for m in members if m.role == TeamMemberRole.MEMBER}
        self.assertEqual(member_ids, {self.applicant1.id, self.applicant2.id})

        # Kiểm tra notifications
        notifs = self.db.query(Notification).all()
        # Phải có thông báo cho Captain và 2 thành viên
        recipient_ids = {n.recipient_id for n in notifs}
        self.assertIn(self.owner.id, recipient_ids)
        self.assertIn(self.applicant1.id, recipient_ids)
        self.assertIn(self.applicant2.id, recipient_ids)

    def test_create_team_forbidden_for_non_owner(self):
        """Người không phải chủ bài đăng không được tạo đội (403 Forbidden)."""
        with self.assertRaises(HTTPException) as ctx:
            create_team_from_full_post(
                db=self.db,
                post_id=self.full_post.id,
                current_user_id=self.stranger.id,
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Chỉ chủ bài đăng", ctx.exception.detail)

    def test_create_team_fails_when_post_not_full(self):
        """Bài đăng chưa đủ người (chưa FULL và chưa đủ accepted) bị từ chối 400."""
        # Tạo bài đăng mới chỉ có 0 người chấp nhận trên 3 người cần
        not_full_post = TeamPost(
            id=20,
            user_id=self.owner.id,
            game_id=self.game.id,
            title="Leo Rank Vang",
            needed_players=3,
            play_time="Tối nay",
            region="VN",
            status=PostStatus.OPEN,
            expires_at=datetime.utcnow() + timedelta(days=2),
        )
        self.db.add(not_full_post)
        self.db.commit()

        with self.assertRaises(HTTPException) as ctx:
            create_team_from_full_post(
                db=self.db,
                post_id=not_full_post.id,
                current_user_id=self.owner.id,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Bài đăng chưa đủ người", ctx.exception.detail)

    def test_create_team_handles_duplicate_name_automatically(self):
        """Tự động xử lý thêm hậu tố khi tên đội trùng, không lỗi DB."""
        # Đã có 1 team tên "Team Chien Than"
        existing_team = Team(
            name="Team Chien Than",
            main_game_id=self.game.id,
            captain_id=self.stranger.id,
            max_members=5,
            join_mode=TeamJoinMode.PUBLIC,
        )
        self.db.add(existing_team)
        self.db.commit()

        req = CreateTeamFromPostRequest(name="Team Chien Than")
        result = create_team_from_full_post(
            db=self.db,
            post_id=self.full_post.id,
            current_user_id=self.owner.id,
            data=req,
        )
        # Tên đội phải được disambiguate thành "Team Chien Than #2"
        self.assertEqual(result["team_name"], "Team Chien Than #2")

    def test_api_endpoint_create_team(self):
        """Kiểm tra gọi qua FastAPI TestClient endpoint POST /api/team-posts/{id}/create-team."""
        app = FastAPI()
        app.include_router(team_post_router, prefix="/api")

        # Dependency overrides
        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        def override_get_current_user():
            return self.owner

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        res = client.post(
            f"/api/team-posts/{self.full_post.id}/create-team",
            json={"name": "Api Created Team", "description": "Tạo qua API"},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["team_name"], "Api Created Team")
        self.assertEqual(data["members_count"], 3)
        self.assertEqual(data["captain_id"], self.owner.id)


if __name__ == "__main__":
    unittest.main()
