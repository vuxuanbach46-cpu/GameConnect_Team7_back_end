import unittest

from app.crud.post import _game_names_for_hashtag, _hashtag_matches


class PostSearchTests(unittest.TestCase):
    def test_matches_hashtag_with_hyphen_and_space(self):
        self.assertTrue(
            _hashtag_matches(
                "Tìm đồng đội để leo rank #Counter-Strike 2 nhé!",
                "Counter-Strike 2",
            )
        )

    def test_does_not_match_word_after_hashtag(self):
        self.assertFalse(
            _hashtag_matches(
                "Nội dung về #Counter-Strike 20",
                "Counter-Strike 2",
            )
        )

    def test_matches_hashtag_case_insensitively(self):
        self.assertTrue(
            _hashtag_matches(
                "Đang tìm #counter-strike 2",
                "Counter-Strike 2",
            )
        )

    def test_resolves_counter_strike_game_aliases(self):
        aliases = _game_names_for_hashtag("Counter-Strike 2")
        self.assertIn("counter-strike 2", aliases)
        self.assertIn("cs2", aliases)

    def test_resolves_league_of_legends_aliases(self):
        aliases = _game_names_for_hashtag("League of Legends")
        self.assertIn("league of legends", aliases)
        self.assertIn("liên minh huyền thoại", aliases)


if __name__ == "__main__":
    unittest.main()
