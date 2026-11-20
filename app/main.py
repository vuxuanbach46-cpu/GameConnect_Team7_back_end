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
from starlette.middleware.sessions import SessionMiddleware

from app.routers import auth, gamer_profile, notifications, posts, team_post, users
from app.routers import games, user_games, admin_games, profile_search
from app.routers import matchmaking
from app.core.auth_middleware import AuthMiddleware
from app.routers import reports
from app.routers import friend_request
from app.routers import team_join, team

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        tables = Base.metadata.sorted_tables
        if not tables:
            raise RuntimeError("No SQLAlchemy models are registered in Base.metadata.")

        Base.metadata.create_all(bind=engine, tables=tables, checkfirst=True)
        with engine.begin() as connection:
            table_names_set = set(inspect(connection).get_table_names())
            if "posts" in table_names_set:
                post_columns = {
                    column["name"]
                    for column in inspect(connection).get_columns("posts")
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
                    print(
                        "[DB] Added posts.image_urls and migrated existing image URLs."
                    )

            if "match_rooms" in table_names_set:
                match_rooms_cols = {
                    column["name"]
                    for column in inspect(connection).get_columns("match_rooms")
                }
                if "label" not in match_rooms_cols:
                    connection.execute(
                        text(
                            "ALTER TABLE match_rooms ADD COLUMN label VARCHAR(100) NULL AFTER max_rank_id"
                        )
                    )
                    print("[DB] Added match_rooms.label column.")

            if "gamer_profiles" in table_names_set:
                gp_cols = {
                    column["name"] for column in inspect(connection).get_columns("gamer_profiles")
                }
                if "is_public" not in gp_cols:
                    connection.execute(
                        text("ALTER TABLE gamer_profiles ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT FALSE")
                    )
                    print("[DB] Added gamer_profiles.is_public column.")

            if "users" in table_names_set:
                user_cols = {
                    column["name"]
                    for column in inspect(connection).get_columns("users")
                }
                if "google_id" not in user_cols:
                    connection.execute(
                        text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255) NULL UNIQUE")
                    )
                    print("[DB] Added users.google_id column.")
                if "auth_provider" not in user_cols:
                    connection.execute(
                        text("ALTER TABLE users ADD COLUMN auth_provider ENUM('LOCAL', 'GOOGLE') NOT NULL DEFAULT 'LOCAL'")
                    )
                    print("[DB] Added users.auth_provider column.")
                connection.execute(
                    text("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NULL")
                )

        table_names = ", ".join(table.name for table in tables)
        print(f"[DB] Checked/created {len(tables)} tables: {table_names}")
        print(
            f"[DB] Connected to MySQL {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
    except SQLAlchemyError as error:
        print("[DB] Could not initialize database tables. Check MySQL schema and .env.")
        print(f"[DB] SQLAlchemy error: {error}")
    except RuntimeError as error:
        print(f"[DB] Model registration error: {error}")
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.state.limiter = limiter
register_exception_handlers(app)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    same_site="lax",
    https_only=False,
)

# CORS: cho phép trang FE (khác cổng/khác domain) gọi được API này
origins = settings.cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$" if "*" in origins else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(gamer_profile.router)
app.include_router(friend_request.router)
app.include_router(notifications.router)
app.include_router(team_post.router, prefix="/api")
app.include_router(matchmaking.router, prefix="/api")
app.include_router(posts.router)
app.include_router(games.router)
app.include_router(user_games.router)
app.include_router(admin_games.router)
app.include_router(team_join.router)
app.include_router(reports.router)
app.include_router(team_join.router, prefix="/api")
app.add_middleware(AuthMiddleware)
app.include_router(team.router, prefix="/api")
app.include_router(profile_search.router)


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} đang chạy. Xem tài liệu API tại /docs"}
app.include_router(reports.public_router)
