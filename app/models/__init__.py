
# Import models so SQLAlchemy can resolve relationships and create their tables.
from app.models.user import User
from app.models.gamer_profile import GamerProfile
from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.models.user_game import UserGame
from app.models.friend_request import FriendRequest
from app.models.friendships import Friendship
from app.models.block import Block
from app.models.team_post import TeamPost, TeamPostApplication, TeamPostRole

from app.models.post import Post
from app.models.post_game import PostGame
from app.models.comment import Comment
from app.models.post_like import PostLike
from app.models.notification import Notification

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_join_request import TeamJoinRequest
