"""Điểm khởi động của backend.

Chạy:  uvicorn app.main:app --reload
Tài liệu API tự sinh: http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from app import models  # noqa: F401 - import để SQLAlchemy biết các bảng
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.limiter import limiter
from app.db.session import Base, engine
from app.routers import friend_request
from app.routers import auth, gamer_profile, notifications, posts, team_post, users
from app.core.auth_middleware import AuthMiddleware
from app.routers import team_join
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        tables = Base.metadata.sorted_tables
        if not tables:
            raise RuntimeError("No SQLAlchemy models are registered in Base.metadata.")

        Base.metadata.create_all(bind=engine, tables=tables, checkfirst=True)
        with engine.begin() as connection:
            post_columns = {
                column["name"] for column in inspect(connection).get_columns("posts")
            }
            if "image_urls" not in post_columns:
                connection.execute(
                    text("ALTER TABLE posts ADD COLUMN image_urls JSON NULL")
                )
                connection.execute(
                    text(
                        "UPDATE posts "
                        "SET image_urls = JSON_ARRAY(image_url) "
                        "WHERE image_url IS NOT NULL AND image_url <> ''"
                    )
                )
                print("[DB] Added posts.image_urls and migrated existing image URLs.")

        table_names = ", ".join(table.name for table in tables)
        print(f"[DB] Checked/created {len(tables)} tables: {table_names}")
        print(f"[DB] Connected to MySQL {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    except SQLAlchemyError as error:
        print("[DB] Could not initialize database tables. Check MySQL schema and .env.")
        print(f"[DB] SQLAlchemy error: {error}")
    except RuntimeError as error:
        print(f"[DB] Model registration error: {error}")
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.state.limiter = limiter
register_exception_handlers(app)

# CORS: cho phép trang FE (khác cổng/khác domain) gọi được API này
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(friend_request.router)
app.include_router(notifications.router)
app.include_router(gamer_profile.router)
app.include_router(team_post.router, prefix="/api")
app.include_router(posts.router)
app.include_router(team_join.router)
app.add_middleware(AuthMiddleware)


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} đang chạy. Xem tài liệu API tại /docs"}
