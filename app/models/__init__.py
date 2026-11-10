# Import models so SQLAlchemy can resolve relationships and create their tables.
from app.models.user import User  # noqa: F401
from app.models.gamer_profile import GamerProfile  # noqa: F401
from app.models.game import Game  # noqa: F401
from app.models.game_rank import GameRank  # noqa: F401
from app.models.game_role import GameRole  # noqa: F401
from app.models.user_game import UserGame  # noqa: F401
from app.models.team_post import TeamPost, TeamPostApplication, TeamPostRole  # noqa: F401
from app.models.post import Post  # noqa: F401
from app.models.post_game import PostGame  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.post_like import PostLike  # noqa: F401
