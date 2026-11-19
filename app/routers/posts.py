from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_admin_user, get_current_user, get_optional_user
from app.crud import comment as comment_crud
from app.crud import post as post_crud
from app.crud import post_like as post_like_crud
from app.db.session import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.api_response import api_repoint
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate
from app.schemas.post import PostCreate, PostOut, PostUpdate
from app.schemas.post_like import PostLikeOut

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


def _post_list_response(
    req: Request, db: Session, posts: list[Post], message: str
):
    counts = post_crud.get_post_counts_by_id(db, [post.id for post in posts])
    results = [
        _post_response(post, *counts[post.id]).model_dump(mode="json")
        for post in posts
    ]
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=message,
        data=results,
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
            detail="Chỉ tác giả mới được sửa bài viết",
        )


def _require_author_or_admin(post: Post, current_user: User) -> None:
    if post.user_id != current_user.id:
        get_admin_user(current_user)


def _comment_or_404(db: Session, post_id: int, comment_id: int) -> Comment:
    comment = comment_crud.get_comment(db, comment_id)
    if comment is None or comment.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bình luận",
        )
    return comment


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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
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
    current_user: User | None = Depends(get_optional_user),
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
    return _post_list_response(req, db, posts, "Lấy danh sách bài viết thành công")


@router.get("/featured", summary="Bài viết nổi bật trong 7 ngày")
def list_featured_posts(
    req: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    posts = post_crud.get_featured_posts(
        db,
        current_user_id=current_user.id if current_user else None,
        skip=skip,
        limit=limit,
    )
    return _post_list_response(req, db, posts, "Lấy bài viết nổi bật thành công")


@router.get("/search", summary="Tìm kiếm bài viết")
def search_posts(
    req: Request,
    keyword: str | None = Query(default=None, min_length=1, max_length=100),
    hashtag: str | None = Query(default=None, min_length=1, max_length=100),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    keyword = keyword.strip() if keyword is not None else None
    hashtag = hashtag.strip().lstrip("#") if hashtag is not None else None
    if not keyword and not hashtag:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cần cung cấp keyword hoặc hashtag",
        )
    posts = post_crud.search_posts(
        db,
        keyword=keyword or None,
        hashtag=hashtag or None,
        current_user_id=current_user.id if current_user else None,
        skip=skip,
        limit=limit,
    )
    return _post_list_response(req, db, posts, "Tìm kiếm bài viết thành công")


@router.get("/{post_id}", summary="Chi tiết bài viết")
def read_post(
    req: Request,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
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
    _require_author_or_admin(post, current_user)
    post_crud.delete_post(db, post)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Xóa bài viết thành công",
        data={"id": post_id},
    )


@router.get("/{post_id}/comments", summary="Danh sách bình luận")
def list_comments(
    req: Request,
    post_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    _post_or_404(db, post_id)
    comments = comment_crud.get_comments(db, post_id, skip=skip, limit=limit)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy danh sách bình luận thành công",
        data=[
            CommentOut.model_validate(comment).model_dump(mode="json")
            for comment in comments
        ],
    )


@router.post(
    "/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
    summary="Thêm bình luận hoặc trả lời",
)
def create_comment(
    req: Request,
    post_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    try:
        comment = comment_crud.create_comment(db, post, current_user.id, data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Thêm bình luận thành công",
        data=CommentOut.model_validate(comment).model_dump(mode="json"),
    )


@router.put(
    "/{post_id}/comments/{comment_id}", summary="Cập nhật bình luận"
)
def edit_comment(
    req: Request,
    post_id: int,
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _post_or_404(db, post_id)
    comment = _comment_or_404(db, post_id, comment_id)
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tạo bình luận mới được sửa",
        )
    comment = comment_crud.update_comment(db, comment, data)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Cập nhật bình luận thành công",
        data=CommentOut.model_validate(comment).model_dump(mode="json"),
    )


@router.delete(
    "/{post_id}/comments/{comment_id}", summary="Xóa bình luận"
)
def remove_comment(
    req: Request,
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _post_or_404(db, post_id)
    comment = _comment_or_404(db, post_id, comment_id)
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tạo bình luận mới được xóa",
        )
    comment_crud.delete_comment(db, comment)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Xóa bình luận thành công",
        data={"id": comment_id},
    )


@router.post("/{post_id}/like", summary="Thích bài viết")
def like_post(
    req: Request,
    response: Response,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = _post_or_404(db, post_id)
    like, created = post_like_crud.create_post_like(db, post, current_user.id)
    response_status = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    response.status_code = response_status
    return api_repoint(
        req=req,
        status_code=response_status,
        message="Thích bài viết thành công",
        data={
            "liked": True,
            "like": PostLikeOut.model_validate(like).model_dump(mode="json"),
        },
    )


@router.delete("/{post_id}/like", summary="Bỏ thích bài viết")
def unlike_post(
    req: Request,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _post_or_404(db, post_id)
    post_like_crud.delete_post_like(db, post_id, current_user.id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Bỏ thích bài viết thành công",
        data={"liked": False},
    )
