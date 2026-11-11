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
from app import models  # noqa: F401 - import để SQLAlchemy biết các bảng
from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import Base, engine
from app.routers import users
from app.routers import gamer_profile
from app.routers import auth, team_post, users, team

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tự tạo các bảng còn thiếu khi server khởi động (bảng đã có thì bỏ qua).
    # Lưu ý: create_all KHÔNG sửa bảng đã tồn tại. Đổi cột -> sửa bằng SQL hoặc xoá bảng tạo lại.
    try:
        Base.metadata.create_all(bind=engine)
        print(f"[DB] Connected to MySQL {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    except OperationalError as error:
        print("[DB] Could not connect to MySQL. Check that MySQL is running and verify .env.")
        if "Unknown database" in str(error.orig):
            print("[DB] Database does not exist. Run sql/init.sql in MySQL Workbench.")
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
app.include_router(team.router, prefix="/api")
app.include_router(team_post.router, prefix="/api")

@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} đang chạy. Xem tài liệu API tại /docs"}
