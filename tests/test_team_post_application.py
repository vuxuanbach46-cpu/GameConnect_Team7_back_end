"""Unit tests verifying task T3CCE5B business logic.
- Gửi ứng tuyển kèm lời nhắn
- Không ứng tuyển bài của chính mình
- Không gửi trùng đơn
- Chủ bài chấp nhận / từ chối
- Đủ người thì bài chuyển FULL
- Mở lại OPEN nếu hủy/từ chối khi đang FULL
- Gửi thông báo qua module Thông báo
"""
import sys
import unittest
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup test in-memory SQLite database
from app.db.session import Base
from app.models.user import User, UserRole, UserStatus
from app.models.game import Game
from app.models.notification import Notification
from app.models.team_post import (
    ApplicationStatus,
    PostStatus,
    TeamPost,
    TeamPostApplication,
)
from app.schemas.team_post import (
    TeamPostApplicationCreate,
    TeamPostApplicationUpdate,
)
from app.crud.team_post import (
    create_application,
    update_application_status,
    delete_application,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.team_post import router as team_post_router
from app.db.session import get_db
from app.core.security import get_current_user

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine)

class TestTeamPostApplicationWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = TestSession()
        # Seed users
        self.owner = User(id=1, email="owner@test.com", username="owner_user", role=UserRole.USER, status=UserStatus.ACTIVE)
        self.applicant1 = User(id=2, email="app1@test.com", username="applicant1", role=UserRole.USER, status=UserStatus.ACTIVE)
        self.applicant2 = User(id=3, email="app2@test.com", username="applicant2", role=UserRole.USER, status=UserStatus.ACTIVE)
        self.admin = User(id=99, email="admin@test.com", username="admin_user", role=UserRole.ADMIN, status=UserStatus.ACTIVE)
        self.db.add_all([self.owner, self.applicant1, self.applicant2, self.admin])

        # Seed game
        self.game = Game(id=1, name="League of Legends", genre="MOBA")
        self.db.add(self.game)

        # Seed team post: needed_players = 2
        self.post = TeamPost(
            id=10,
            user_id=1,
            game_id=1,
            title="Tuyển đồng đội leo rank",
            needed_players=2,
            status=PostStatus.OPEN,
            expires_at=datetime.now() + timedelta(days=2),
        )
        self.db.add(self.post)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.query(Notification).delete()
        self.db.query(TeamPostApplication).delete()
        self.db.query(TeamPost).delete()
        self.db.query(Game).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    def test_apply_to_own_post_forbidden(self):
        """1. Không thể tự ứng tuyển vào bài đăng của chính mình"""
        with self.assertRaises(HTTPException) as ctx:
            create_application(
                self.db,
                team_post_id=self.post.id,
                user_id=self.owner.id,
                data=TeamPostApplicationCreate(message="Tự ứng tuyển"),
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("chính mình", ctx.exception.detail)

    def test_apply_success_and_notify_owner(self):
        """2. Gửi ứng tuyển kèm lời nhắn & gửi thông báo cho chủ bài"""
        data = TeamPostApplicationCreate(message="Mình xin 1 slot jungle nhé!")
        app = create_application(self.db, self.post.id, self.applicant1.id, data)

        self.assertIsNotNone(app.id)
        self.assertEqual(app.status, ApplicationStatus.PENDING)
        self.assertEqual(app.message, "Mình xin 1 slot jungle nhé!")

        # Check notification sent to owner
        notifs = self.db.query(Notification).filter_by(recipient_id=self.owner.id).all()
        self.assertEqual(len(notifs), 1)
        self.assertEqual(notifs[0].type, "TEAM_POST_APPLICATION")
        self.assertIn("Tuyển đồng đội leo rank", notifs[0].content)

    def test_duplicate_application_forbidden(self):
        """3. Không được gửi đơn trùng lặp khi đang PENDING hoặc ACCEPTED"""
        data = TeamPostApplicationCreate(message="Slot 1")
        create_application(self.db, self.post.id, self.applicant1.id, data)

        with self.assertRaises(HTTPException) as ctx:
            create_application(self.db, self.post.id, self.applicant1.id, data)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Bạn đã gửi đơn ứng tuyển", ctx.exception.detail)

    def test_accept_applications_until_full(self):
        """4. Chủ bài chấp nhận đơn; khi đủ người (2/2) thì bài tự động chuyển sang FULL"""
        app1 = create_application(self.db, self.post.id, self.applicant1.id, TeamPostApplicationCreate(message="App 1"))
        app2 = create_application(self.db, self.post.id, self.applicant2.id, TeamPostApplicationCreate(message="App 2"))

        # Owner accepts applicant 1 (1/2 needed)
        update_application_status(
            self.db,
            app1,
            TeamPostApplicationUpdate(status=ApplicationStatus.ACCEPTED),
            self.owner,
        )
        self.db.refresh(self.post)
        self.assertEqual(app1.status, ApplicationStatus.ACCEPTED)
        self.assertEqual(self.post.status, PostStatus.OPEN)

        # Notification sent to applicant 1
        notif1 = self.db.query(Notification).filter_by(recipient_id=self.applicant1.id).first()
        self.assertIsNotNone(notif1)
        self.assertEqual(notif1.type, "TEAM_POST_APPLICATION_ACCEPTED")

        # Owner accepts applicant 2 (2/2 needed -> FULL)
        update_application_status(
            self.db,
            app2,
            TeamPostApplicationUpdate(status=ApplicationStatus.ACCEPTED),
            self.owner,
        )
        self.db.refresh(self.post)
        self.assertEqual(app2.status, ApplicationStatus.ACCEPTED)
        self.assertEqual(self.post.status, PostStatus.FULL)

        # Cannot accept another if already at limit
        user3 = User(id=4, email="app3@test.com", username="applicant3", role=UserRole.USER, status=UserStatus.ACTIVE)
        self.db.add(user3)
        self.db.commit()
        app3 = TeamPostApplication(team_post_id=self.post.id, user_id=4, status=ApplicationStatus.PENDING)
        self.db.add(app3)
        self.db.commit()

        with self.assertRaises(HTTPException) as ctx:
            update_application_status(
                self.db,
                app3,
                TeamPostApplicationUpdate(status=ApplicationStatus.ACCEPTED),
                self.owner,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("đủ số người", ctx.exception.detail)

    def test_reject_application_and_notify(self):
        """5. Chủ bài từ chối đơn & gửi thông báo REJECTED"""
        app1 = create_application(self.db, self.post.id, self.applicant1.id, TeamPostApplicationCreate(message="App 1"))
        update_application_status(
            self.db,
            app1,
            TeamPostApplicationUpdate(status=ApplicationStatus.REJECTED),
            self.owner,
        )
        self.assertEqual(app1.status, ApplicationStatus.REJECTED)

        notif = self.db.query(Notification).filter_by(recipient_id=self.applicant1.id, type="TEAM_POST_APPLICATION_REJECTED").first()
        self.assertIsNotNone(notif)
        self.assertIn("từ chối", notif.content)

    def test_reopen_post_when_accepted_applicant_cancels_or_rejected(self):
        """6. Khi bài đang FULL mà 1 người ACCEPTED rút đơn hoặc bị từ chối thì bài tự động mở lại OPEN"""
        app1 = create_application(self.db, self.post.id, self.applicant1.id, TeamPostApplicationCreate(message="App 1"))
        app2 = create_application(self.db, self.post.id, self.applicant2.id, TeamPostApplicationCreate(message="App 2"))

        update_application_status(self.db, app1, TeamPostApplicationUpdate(status=ApplicationStatus.ACCEPTED), self.owner)
        update_application_status(self.db, app2, TeamPostApplicationUpdate(status=ApplicationStatus.ACCEPTED), self.owner)
        self.db.refresh(self.post)
        self.assertEqual(self.post.status, PostStatus.FULL)

        # Applicant 2 cancels their application
        update_application_status(self.db, app2, TeamPostApplicationUpdate(status=ApplicationStatus.CANCELLED), self.applicant2)
        self.db.refresh(self.post)
        self.assertEqual(self.post.status, PostStatus.OPEN)

        # Owner gets notification about cancellation
        cancel_notif = self.db.query(Notification).filter_by(recipient_id=self.owner.id, type="TEAM_POST_APPLICATION_CANCELLED").first()
        self.assertIsNotNone(cancel_notif)

    def test_reapply_after_cancelled(self):
        """7. Cho phép gửi lại đơn sau khi đã CANCELLED trước đó"""
        app1 = create_application(self.db, self.post.id, self.applicant1.id, TeamPostApplicationCreate(message="App 1"))
        update_application_status(self.db, app1, TeamPostApplicationUpdate(status=ApplicationStatus.CANCELLED), self.applicant1)

        # Re-apply
        re_app = create_application(self.db, self.post.id, self.applicant1.id, TeamPostApplicationCreate(message="Đơn mới sau khi hủy"))
        self.assertEqual(re_app.id, app1.id)
        self.assertEqual(re_app.status, ApplicationStatus.PENDING)
        self.assertEqual(re_app.message, "Đơn mới sau khi hủy")

    def test_api_endpoints_via_testclient(self):
        """8. Test full HTTP API workflow with FastAPI TestClient"""
        test_app = FastAPI()
        test_app.include_router(team_post_router)

        client = TestClient(test_app)

        current_auth_user = {"user": self.applicant1}
        def override_get_db():
            yield self.db
        def override_get_current_user():
            return current_auth_user["user"]

        test_app.dependency_overrides[get_db] = override_get_db
        test_app.dependency_overrides[get_current_user] = override_get_current_user

        # 1. Applicant1 applies via POST /team-posts/{id}/applications
        resp = client.post(
            f"/team-posts/{self.post.id}/applications",
            json={"message": "Xin chao chu bai!"},
        )
        self.assertEqual(resp.status_code, 201)
        app1_data = resp.json()
        app1_id = app1_data["id"]
        self.assertEqual(app1_data["status"], "PENDING")
        self.assertEqual(app1_data["message"], "Xin chao chu bai!")

        # 2. Cannot apply again (duplicate)
        dup_resp = client.post(
            f"/team-posts/{self.post.id}/applications",
            json={"message": "Xin chao lan 2"},
        )
        self.assertEqual(dup_resp.status_code, 400)

        # 3. Post owner lists applications
        current_auth_user["user"] = self.owner
        list_resp = client.get(f"/team-posts/{self.post.id}/applications")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.json()), 1)

        # 4. Post owner accepts application
        update_resp = client.put(
            f"/team-posts/{self.post.id}/applications/{app1_id}",
            json={"status": "ACCEPTED"},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()["status"], "ACCEPTED")

        # 5. Applicant2 applies
        current_auth_user["user"] = self.applicant2
        resp2 = client.post(
            f"/team-posts/{self.post.id}/applications",
            json={"message": "Slot cuoi cung!"},
        )
        self.assertEqual(resp2.status_code, 201)
        app2_id = resp2.json()["id"]

        # 6. Post owner accepts applicant2 -> Post becomes FULL
        current_auth_user["user"] = self.owner
        update_resp2 = client.put(
            f"/team-posts/{self.post.id}/applications/{app2_id}",
            json={"status": "ACCEPTED"},
        )
        self.assertEqual(update_resp2.status_code, 200)

        # Verify post is now FULL
        self.db.refresh(self.post)
        self.assertEqual(self.post.status, PostStatus.FULL)

        # 7. Applicant2 cancels application -> Post reverts to OPEN
        current_auth_user["user"] = self.applicant2
        cancel_resp = client.put(
            f"/team-posts/{self.post.id}/applications/{app2_id}",
            json={"status": "CANCELLED"},
        )
        self.assertEqual(cancel_resp.status_code, 200)
        self.db.refresh(self.post)
        self.assertEqual(self.post.status, PostStatus.OPEN)

if __name__ == "__main__":
    unittest.main()
