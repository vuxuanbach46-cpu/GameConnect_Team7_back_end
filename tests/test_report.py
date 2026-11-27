import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.models.report import Report
from app.models.user import User
from app.models.post import Post
from app.schemas.report import ReportCreate, ReportReason, ReportTargetType
from app.routers.reports import submit_report, TARGET_MODELS


class ReportEndpointTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.req = MagicMock()
        self.current_user = User(id=10, username="test_user")

    def test_cannot_report_own_account(self):
        info = ReportCreate(
            target_type=ReportTargetType.USER,
            target_id=10,
            reason=ReportReason.SPAM,
            description="Tự báo cáo mình"
        )
        self.db.query().filter().first.return_value = self.current_user

        with self.assertRaises(HTTPException) as ctx:
            submit_report(self.req, info, self.db, self.current_user)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("chính tài khoản", ctx.exception.detail)

    def test_cannot_report_own_post(self):
        own_post = Post(id=5, user_id=10, content="My post")
        info = ReportCreate(
            target_type=ReportTargetType.POST,
            target_id=5,
            reason=ReportReason.HARASSMENT
        )
        self.db.query().filter().first.return_value = own_post

        with self.assertRaises(HTTPException) as ctx:
            submit_report(self.req, info, self.db, self.current_user)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("chính mình", ctx.exception.detail)

    def test_cannot_report_same_target_twice(self):
        other_user = User(id=20, username="other_user")
        existing_report = Report(id=1, reporter_id=10, target_type="USER", target_id=20)

        info = ReportCreate(
            target_type=ReportTargetType.USER,
            target_id=20,
            reason=ReportReason.SCAM
        )
        # First query checks target exists -> returns other_user
        # Second query checks existed report -> returns existing_report
        self.db.query().filter().first.side_effect = [other_user, existing_report]

        with self.assertRaises(HTTPException) as ctx:
            submit_report(self.req, info, self.db, self.current_user)

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("đã báo cáo đối tượng này rồi", ctx.exception.detail)

    def test_report_nonexistent_target_raises_404(self):
        info = ReportCreate(
            target_type=ReportTargetType.POST,
            target_id=999,
            reason=ReportReason.OTHER
        )
        self.db.query().filter().first.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            submit_report(self.req, info, self.db, self.current_user)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("không tồn tại", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
