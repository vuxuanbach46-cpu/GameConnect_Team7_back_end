from app.db.session import SessionLocal
from app.models.post import Post, PostStatus


def seed_posts():
    db = SessionLocal()
    try:
        if db.query(Post).count() == 0:
            posts = []
            for i in range(1, 31):
                post = Post(
                    user_id=1,
                    content=f"Đây là bài viết chia sẻ kinh nghiệm leo rank số {i} của cộng đồng GameConnect!",
                    status=PostStatus.VISIBLE.value,
                )
                posts.append(post)

            db.bulk_save_objects(posts)
            db.commit()
            print(" Seeded 30 posts successfully!")
        else:
            print("Posts table is not empty. Skipping seed.")
    except Exception as error:
        print(f"Error seeding: {error}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_posts()
