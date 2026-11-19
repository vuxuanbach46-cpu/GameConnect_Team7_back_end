"""Unit tests cho API Gợi ý bài đăng phù hợp theo game và rank (T3CCE98) dùng unittest chuẩn."""
from datetime import datetime, timedelta
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.user import User
from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.user_game import UserGame
from app.models.team_post import TeamPost, PostStatus
from app.crud.team_post import get_recommended_team_posts


class TestTeamPostRecommendations(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Seed Games
        lol = Game(id=1, name="League of Legends", genre="MOBA")
        val = Game(id=2, name="Valorant", genre="FPS")
        self.session.add_all([lol, val])
        self.session.commit()

        # Seed Ranks for LoL: Silver (1), Gold (2), Platinum (3), Diamond (4)
        r_silver = GameRank(id=1, game_id=1, rank_name="Silver", rank_order=1)
        r_gold = GameRank(id=2, game_id=1, rank_name="Gold", rank_order=2)
        r_plat = GameRank(id=3, game_id=1, rank_name="Platinum", rank_order=3)
        r_dia = GameRank(id=4, game_id=1, rank_name="Diamond", rank_order=4)

        # Seed Ranks for Valorant: Iron (1), Bronze (2), Silver (3), Gold (4)
        v_iron = GameRank(id=5, game_id=2, rank_name="Iron", rank_order=1)
        v_bronze = GameRank(id=6, game_id=2, rank_name="Bronze", rank_order=2)
        v_silver = GameRank(id=7, game_id=2, rank_name="Silver", rank_order=3)
        v_gold = GameRank(id=8, game_id=2, rank_name="Gold", rank_order=4)

        self.session.add_all([r_silver, r_gold, r_plat, r_dia, v_iron, v_bronze, v_silver, v_gold])
        self.session.commit()

        # Seed Users
        u1 = User(id=1, email="player1@test.com", username="player1")
        u2 = User(id=2, email="player2@test.com", username="player2")
        u3 = User(id=3, email="player3@test.com", username="player3")
        self.session.add_all([u1, u2, u3])
        self.session.commit()

        # User 1 plays LoL at Platinum (rank_id=3)
        ug1 = UserGame(user_id=1, game_id=1, rank_id=3)
        self.session.add(ug1)
        self.session.commit()

    def tearDown(self):
        self.session.close()

    def test_recommendation_matches_game_and_rank(self):
        """Bài đăng LoL yêu cầu Gold -> Diamond phải khớp với user rank Platinum (3)."""
        p1 = TeamPost(
            id=1,
            user_id=2,
            game_id=1,
            title="LoL Flex Team leo Plat/Dia",
            min_rank_id=2,
            max_rank_id=4,
            needed_players=2,
            status=PostStatus.OPEN,
        )
        p2 = TeamPost(
            id=2,
            user_id=2,
            game_id=1,
            title="LoL Newbie leo Vang",
            min_rank_id=1,
            max_rank_id=2,
            needed_players=1,
            status=PostStatus.OPEN,
        )
        p3 = TeamPost(
            id=3,
            user_id=2,
            game_id=2,
            title="Val Unrated",
            min_rank_id=5,
            max_rank_id=6,
            needed_players=2,
            status=PostStatus.OPEN,
        )
        self.session.add_all([p1, p2, p3])
        self.session.commit()

        posts, has_profile, labels = get_recommended_team_posts(self.session, user_id=1, limit=1)

        self.assertTrue(has_profile)
        self.assertIn("League of Legends (Platinum)", labels)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].id, 1)
        self.assertIn("Rank Platinum", getattr(posts[0], "match_reason", ""))

    def test_recommendation_excludes_own_posts(self):
        """Không gợi ý bài do chính người dùng tạo."""
        p_own = TeamPost(
            id=10,
            user_id=1,
            game_id=1,
            title="Bài của tôi",
            min_rank_id=2,
            max_rank_id=4,
            needed_players=1,
            status=PostStatus.OPEN,
        )
        p_other = TeamPost(
            id=11,
            user_id=3,
            game_id=1,
            title="Bài người khác",
            min_rank_id=2,
            max_rank_id=4,
            needed_players=1,
            status=PostStatus.OPEN,
        )
        self.session.add_all([p_own, p_other])
        self.session.commit()

        posts, _, _ = get_recommended_team_posts(self.session, user_id=1, limit=10)
        post_ids = [p.id for p in posts]
        self.assertNotIn(10, post_ids)
        self.assertIn(11, post_ids)

    def test_recommendation_excludes_closed_or_expired(self):
        """Không gợi ý bài đã CLOSED hoặc hết hạn."""
        p_closed = TeamPost(
            id=20,
            user_id=2,
            game_id=1,
            title="Bài đã đóng",
            min_rank_id=2,
            max_rank_id=4,
            needed_players=1,
            status=PostStatus.CLOSED,
        )
        p_expired = TeamPost(
            id=21,
            user_id=2,
            game_id=1,
            title="Bài hết hạn",
            min_rank_id=2,
            max_rank_id=4,
            needed_players=1,
            status=PostStatus.OPEN,
            expires_at=datetime.now() - timedelta(hours=1),
        )
        self.session.add_all([p_closed, p_expired])
        self.session.commit()

        posts, _, _ = get_recommended_team_posts(self.session, user_id=1, limit=10)
        post_ids = [p.id for p in posts]
        self.assertNotIn(20, post_ids)
        self.assertNotIn(21, post_ids)


if __name__ == "__main__":
    unittest.main()
