from app.db.session import Base, SessionLocal, engine
from app.models.community import User
from app.models.post import Post, PostStatus


def seed_posts():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.id == 1).first() is None:
            db.add(User(id=1, username="gameconnect_admin"))
            db.commit()

        post_contents = [
            "Tìm đồng đội leo rank Valo tối nay.",
            "Chia sẻ kinh nghiệm farm tiền trong game.",
            "Review trận đấu đáng nhớ trong tuần.",
            "Xin tư vấn build nhân vật mới.",
            "Tổng hợp mẹo chơi nhanh cho người mới.",
            "Tìm team tham gia giải đấu cuối tuần.",
            "Thảo luận meta và cập nhật bản mới.",
            "Chia sẻ cảnh đẹp trong game.",
        ]

        if db.query(Post).count() == 0:
            posts = []
            for i in range(1, 31):
                post = Post(
                    user_id=1,
                    content=f"{post_contents[(i - 1) % len(post_contents)]} (Bài {i})",
                    status=PostStatus.VISIBLE.value,
                )
                posts.append(post)

            db.bulk_save_objects(posts)
            db.commit()
            print(" Seeded 30 posts successfully!")
        else:
            for i in range(1, 31):
                post = db.query(Post).filter(Post.id == i).first()
                if post and post.content.startswith("Đây là bài viết chia sẻ kinh nghiệm leo rank"):
                    post.content = (
                        f"{post_contents[(i - 1) % len(post_contents)]} (Bài {i})"
                    )
            db.commit()
            print("Updated 30 seeded post contents successfully!")
    except Exception as error:
        print(f"Error seeding: {error}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_posts()
