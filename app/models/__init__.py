# Import mọi model ở đây để Base.metadata.create_all() "nhìn thấy" và tạo bảng.
# Thêm model mới -> nhớ thêm 1 dòng import vào file này.
# from app.models.item import Item  # noqa: F401
from app.models.gamer_profile import GamerProfile
from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.models.user_game import UserGame