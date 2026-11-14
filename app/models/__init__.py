# Import models so SQLAlchemy can resolve relationships and create their tables.
from app.models.user import User  # noqa: F401
from app.models.gamer_profile import GamerProfile  # noqa: F401
from app.models.game import Game  # noqa: F401
from app.models.game_rank import GameRank  # noqa: F401
from app.models.game_role import GameRole  # noqa: F401
from app.models.user_game import UserGame  # noqa: F401
from app.models.friend_request import FriendRequest
from app.models.friendships import Friendship
from app.models.block import Block
from app.models.report import Report  # noqa: F401
from app.models.team import Team  # noqa: F401
from app.models.team_member import TeamMember  # noqa: F401
from app.models.team_join_request import TeamJoinRequest  # noqa: F401
from app.models.team_post import TeamPost, TeamPostApplication, TeamPostRole  # noqa: F401
from app.models.post import Post  # noqa: F401
from app.models.post_game import PostGame  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.post_like import PostLike  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.matchmaking import MatchRoom, MatchRoomMember, MatchQueue  # noqa: F401
from app.models.revoked_token import RevokedToken  # noqa: F401
