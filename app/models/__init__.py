# Import mọi model ở đây để Base.metadata.create_all() "nhìn thấy" và tạo bảng.
# Thêm model mới -> nhớ thêm 1 dòng import vào file này.
from app.models.user import User  # noqa: F401
from app.models.gamer_profile import GamerProfile  # noqa: F401
from app.models.game import Game  # noqa: F401
from app.models.game_rank import GameRank  # noqa: F401
from app.models.game_role import GameRole  # noqa: F401
from app.models.user_game import UserGame  # noqa: F401
from app.models.team_post import TeamPost, TeamPostApplication, TeamPostRole  # noqa: F401
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_join_request import TeamJoinRequest