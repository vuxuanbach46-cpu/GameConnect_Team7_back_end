import asyncio
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
from starlette.datastructures import Headers

from app.crud.image_upload import MAX_IMAGE_SIZE, save_uploaded_image
from app.schemas.post import PostCreate, PostUpdate


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def make_upload(content_type: str, content: bytes) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename="community.png",
        headers=Headers({"content-type": content_type}),
    )


class CommunityImageUploadTests(unittest.TestCase):
    def test_saves_valid_png_with_short_storage_url(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory)
            filename = asyncio.run(
                save_uploaded_image(
                    make_upload("image/png", PNG_SIGNATURE + b"image"), destination
                )
            )

            self.assertTrue(filename.endswith(".png"))
            self.assertEqual(
                (destination / filename).read_bytes(), PNG_SIGNATURE + b"image"
            )
            self.assertLess(len(f"/uploads/posts/{filename}"), 500)

    def test_rejects_mismatched_image_signature(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(HTTPException) as error:
                asyncio.run(
                    save_uploaded_image(
                        make_upload("image/png", b"not a png"), Path(directory)
                    )
                )

            self.assertEqual(error.exception.status_code, 400)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_rejects_image_larger_than_limit(self):
        oversized = PNG_SIGNATURE + b"x" * MAX_IMAGE_SIZE

        with TemporaryDirectory() as directory:
            with self.assertRaises(HTTPException) as error:
                asyncio.run(
                    save_uploaded_image(
                        make_upload("image/png", oversized), Path(directory)
                    )
                )
            self.assertEqual(error.exception.status_code, 400)

    def test_post_schemas_reject_malformed_image_references(self):
        with self.assertRaises(ValidationError):
            PostCreate(content="Bad legacy image", image_url="fw3f")
        with self.assertRaises(ValidationError):
            PostUpdate(image_urls=["ươqfqw"])

    def test_post_schemas_accept_uploaded_and_external_image_urls(self):
        created = PostCreate(
            content="Valid uploaded image",
            image_url="/uploads/posts/community.png",
        )
        updated = PostUpdate(image_url="https://cdn.example.test/community.png")

        self.assertEqual(created.image_urls, ["/uploads/posts/community.png"])
        self.assertEqual(updated.image_url, "https://cdn.example.test/community.png")


if __name__ == "__main__":
    unittest.main()
