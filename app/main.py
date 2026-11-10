"""Điểm khởi động của backend.

Chạy:  uvicorn app.main:app --reload
Tài liệu API tự sinh: http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.routers import auth
from app import models  # noqa: F401 - import để SQLAlchemy biết các bảng
from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import Base, engine
from app.models.comment import Comment
from app.models.post import Post
from app.models.post_game import PostGame
from app.models.post_like import PostLike
from app.routers import auth, gamer_profile, posts, team_post, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[
                Post.__table__,
                PostGame.__table__,
                Comment.__table__,
                PostLike.__table__,
            ],
        )
        print(f"[DB] Connected to MySQL {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    except OperationalError as error:
        print("[DB] Could not initialize post tables. Check MySQL schema and .env.")
        print(f"[DB] Details: {error.orig}")
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: cho phép trang FE (khác cổng/khác domain) gọi được API này
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(gamer_profile.router)
app.include_router(team_post.router, prefix="/api")
app.include_router(posts.router)

@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} đang chạy. Xem tài liệu API tại /docs"}
