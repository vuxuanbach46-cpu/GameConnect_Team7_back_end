from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.crud import post as post_crud
from app.db.session import get_db
from app.models.post import Post
from app.models.user import User
from app.schemas.api_response import api_repoint
from app.schemas.post import PostCreate, PostOut, PostUpdate

router = APIRouter(prefix="/posts", tags=["Posts"])


def _post_response(post: Post, like_count: int, comment_count: int) -> PostOut:
    image_urls = post.image_urls or ([post.image_url] if post.image_url else [])
    return PostOut(
        id=post.id,
        user_id=post.user_id,
        content=post.content,
        image_url=post.image_url,
        image_urls=image_urls,
        game_ids=[post_game.game_id for post_game in post.post_games],
        status=post.status,
        created_at=post.created_at,
        updated_at=post.updated_at,
        like_count=like_count,
        comment_count=comment_count,
    )


def _post_or_404(db: Session, post_id: int) -> Post:
    post = post_crud.get_post(db, post_id)
    if post is None or post.status != "VISIBLE":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bài viết",
        )
    return post


def _require_author(post: Post, current_user: User) -> None:
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tác giả mới được sửa hoặc xóa bài viết",
        )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Tạo bài viết")
def create_post(
    req: Request,
    data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        post = post_crud.create_post(db, data, current_user.id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    result = _post_response(post, 0, 0)
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Tạo bài viết thành công",
        data=result.model_dump(mode="json"),
    )


@router.get("", summary="Danh sách bài viết")
def list_posts(
    req: Request,
    game_id: int | None = Query(default=None, ge=1),
    user_id: int | None = Query(default=None, ge=1, description="Lọc bài viết của người dùng"),
    friends_only: bool = Query(default=False, description="Chỉ lấy bài viết của bạn bè"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    posts = post_crud.get_feed_posts(
        db,
        current_user_id=current_user.id,
        game_id=game_id,
        user_id=user_id,
        friends_only=friends_only,
        skip=skip,
        limit=limit,
    )
    counts = post_crud.get_post_counts_by_id(db, [post.id for post in posts])
    results = [
        _post_response(post, *counts[post.id]).model_dump(mode="json")
        for post in posts
    ]
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy danh sách bài viết thành công",
        data=results,
    )


@router.get("/{post_id}", summary="Chi tiết bài viết")
def read_post(req: Request, post_id: int, db: Session = Depends(get_db)):
    post = _post_or_404(db, post_id)
    like_count, comment_count = post_crud.get_post_counts(db, post_id)
    result = _post_response(post, like_count, comment_count)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy bài viết thành công",
        data=result.model_dump(mode="json"),
    )


@router.put("/{post_id}", summary="Cập nhật bài viết")
def update_post(
    req: Request,
    post_id: int,
    data: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = post_crud.get_post(db, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài viết"
        )
    _require_author(post, current_user)
    try:
        post = post_crud.update_post(db, post, data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    like_count, comment_count = post_crud.get_post_counts(db, post_id)
    result = _post_response(post, like_count, comment_count)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Cập nhật bài viết thành công",
        data=result.model_dump(mode="json"),
    )


@router.delete("/{post_id}", summary="Xóa bài viết")
def remove_post(
    req: Request,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = post_crud.get_post(db, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài viết"
        )
    _require_author(post, current_user)
    post_crud.delete_post(db, post)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Xóa bài viết thành công",
        data={"id": post_id},
    )
