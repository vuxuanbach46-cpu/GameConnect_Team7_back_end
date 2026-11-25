from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.security import get_admin_user, get_current_user, get_optional_user
from app.crud import comment as comment_crud
from app.crud.image_upload import save_uploaded_image
from app.crud import post as post_crud
from app.crud import post_like as post_like_crud
from app.db.session import get_db
from app.models.comment import Comment
from app.models.gamer_profile import GamerProfile
from app.models.post import Post
from app.models.post_like import PostLike
from app.models.user import User
from app.schemas.api_response import api_repoint
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate
from app.schemas.post import PostCreate, PostOut, PostUpdate
from app.schemas.post_like import PostLikeOut

router = APIRouter(prefix="/posts", tags=["Posts"])
POST_IMAGE_DIR = Path(__file__).resolve().parent.parent / "uploads" / "posts"


def _author_data_map(db: Session, user_ids: set[int]) -> dict[int, dict]:
    if not user_ids:
        return {}
    rows = (
        db.query(
            User.id,
            User.username,
            GamerProfile.display_name,
            GamerProfile.avatar,
        )
        .outerjoin(GamerProfile, GamerProfile.user_id == User.id)
        .filter(User.id.in_(user_ids))
        .all()
    )
    return {
        row.id: {
            "username": row.username,
            "display_name": row.display_name,
            "avatar": row.avatar,
        }
        for row in rows
    }


def _comment_responses(db: Session, comments: list[Comment]) -> list[dict]:
    authors = _author_data_map(db, {comment.user_id for comment in comments})
    results = []
    for comment in comments:
        author = authors.get(comment.user_id, {})
        result = CommentOut.model_validate(comment).model_dump(mode="json")
        result.update(
            author_name=author.get("display_name") or author.get("username") or f"Game thủ #{comment.user_id}",
            author_username=author.get("username"),
            author_avatar=author.get("avatar"),
        )
        results.append(result)
    return results


def _post_response(
    db: Session,
    post: Post,
    like_count: int,
    comment_count: int,
    author_data: dict | None = None,
    liked_by_current_user: bool = False,
) -> PostOut:
    image_urls = post.image_urls or ([post.image_url] if post.image_url else [])
    if author_data is None:
        author_data = _author_data_map(db, {post.user_id}).get(post.user_id, {})
    username = author_data.get("username")
    return PostOut(
        id=post.id,
        user_id=post.user_id,
        author_name=author_data.get("display_name") or username or f"Game thủ #{post.user_id}",
        author_username=username,
        author_handle=f"@{username}" if username else f"@user{post.user_id}",
        author_avatar=author_data.get("avatar"),
        content=post.content,
        image_url=post.image_url,
        image_urls=image_urls,
        game_ids=[post_game.game_id for post_game in post.post_games],
        status=post.status,
        created_at=post.created_at,
        updated_at=post.updated_at,
        like_count=like_count,
        comment_count=comment_count,
        liked_by_current_user=liked_by_current_user,
    )


def _post_list_response(
    req: Request,
    db: Session,
    posts: list[Post],
    message: str,
    current_user_id: int | None = None,
):
    counts = post_crud.get_post_counts_by_id(db, [post.id for post in posts])
    authors = _author_data_map(db, {post.user_id for post in posts})
    liked_ids = set()
    if current_user_id is not None and posts:
        liked_ids = {
            row[0]
            for row in db.query(PostLike.post_id)
            .filter(
                PostLike.user_id == current_user_id,
                PostLike.post_id.in_([post.id for post in posts]),
            )
            .all()
        }
    results = [
        _post_response(
            db,
            post,
            *counts[post.id],
            author_data=authors.get(post.user_id, {}),
            liked_by_current_user=post.id in liked_ids,
        ).model_dump(mode="json")
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


@router.post("/images", status_code=status.HTTP_201_CREATED, summary="Tải ảnh bài viết lên")
async def upload_post_image(
    req: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    filename = await save_uploaded_image(file, POST_IMAGE_DIR)
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Tải ảnh lên thành công",
        data={"image_url": f"/uploads/posts/{filename}"},
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    result = _post_response(db, post, 0, 0, liked_by_current_user=False)
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
        current_user_id=current_user.id if current_user else None,
        game_id=game_id,
        user_id=user_id,
        friends_only=friends_only,
        skip=skip,
        limit=limit,
    )
    return _post_list_response(
        req,
        db,
        posts,
        "Lấy danh sách bài viết thành công",
        current_user_id=current_user.id if current_user else None,
    )


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
    return _post_list_response(
        req,
        db,
        posts,
        "Lấy bài viết nổi bật thành công",
        current_user_id=current_user.id if current_user else None,
    )


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
    return _post_list_response(
        req,
        db,
        posts,
        "Tìm kiếm bài viết thành công",
        current_user_id=current_user.id if current_user else None,
    )


@router.get("/{post_id}", summary="Chi tiết bài viết")
def read_post(
    req: Request,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    post = _post_or_404(db, post_id)
    like_count, comment_count = post_crud.get_post_counts(db, post_id)
    liked = False
    if current_user:
        liked = db.query(PostLike.id).filter(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id,
        ).first() is not None
    result = _post_response(
        db,
        post,
        like_count,
        comment_count,
        liked_by_current_user=liked,
    )
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
    liked = db.query(PostLike.id).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id,
    ).first() is not None
    result = _post_response(
        db, post, like_count, comment_count, liked_by_current_user=liked
    )
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
        data=_comment_responses(db, comments),
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
        data=_comment_responses(db, [comment])[0],
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
        data=_comment_responses(db, [comment])[0],
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
