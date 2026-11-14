# Notification

## 1. Cấu trúc file

- `app/models/notification.py`: model của bảng `notifications`.
- `app/crud/notification.py`: hàm `create_notification()` để các module nghiệp vụ tạo thông báo.
- `app/routers/notifications.py`: API danh sách, số chưa đọc, đánh dấu một thông báo đã đọc và đánh dấu tất cả đã đọc.
- `app/schemas/api_response.py`: dùng hàm `api_repoint()` để trả response thành công đúng 6 trường.

## 2. Hàm tạo thông báo dùng chung

Import hàm trong module cần tạo thông báo:

```python
from app.crud.notification import create_notification
```

Cách gọi:

```python
notification = create_notification(
    db=db,
    recipient_id=receiver_id,
    type="FRIEND_REQUEST",
    content="Bạn có lời mời kết bạn mới",
    link="/friends/requests/12",
)
```

Các tham số:

| Tham số | Ý nghĩa |
|---|---|
| `db` | SQLAlchemy session hiện tại |
| `recipient_id` | ID người nhận thông báo |
| `type` | Loại thông báo, ví dụ `FRIEND_REQUEST`, `TEAM_APPLICATION`, `COMMENT` |
| `content` | Nội dung hiển thị |
| `link` | Đường dẫn điều hướng, có thể bỏ trống |

Hàm sử dụng `db.add()` và `db.flush()`, **không tự gọi `db.commit()`**. Module gọi hàm phải commit transaction sau khi lưu nghiệp vụ và thông báo.

## 3. Ví dụ gọi từ các module

### 3.1. Lời mời kết bạn

Gọi sau khi tạo bản ghi lời mời kết bạn:

```python
create_notification(
    db=db,
    recipient_id=receiver.id,
    type="FRIEND_REQUEST",
    content=f"{sender.username} đã gửi lời mời kết bạn",
    link=f"/friends/requests/{friend_request.id}",
)

db.commit()
```

### 3.2. Yêu cầu tham gia đội

Gọi sau khi tạo yêu cầu tham gia đội:

```python
create_notification(
    db=db,
    recipient_id=team_owner.id,
    type="TEAM_REQUEST",
    content=f"{sender.username} muốn tham gia đội của bạn",
    link=f"/teams/{team.id}/requests",
)

db.commit()
```

### 3.3. Ứng tuyển bài đăng tìm đội

Gọi sau khi tạo đơn ứng tuyển. Người nhận là chủ bài đăng:

```python
create_notification(
    db=db,
    recipient_id=team_post.user_id,
    type="TEAM_APPLICATION",
    content="Có người vừa ứng tuyển vào bài đăng tìm đội của bạn",
    link=f"/team-posts/{team_post.id}/applications",
)

db.commit()
```

### 3.4. Bình luận bài viết

Gọi sau khi tạo bình luận. Không tự gửi thông báo cho chính người bình luận:

```python
if post.user_id != commenter.id:
    create_notification(
        db=db,
        recipient_id=post.user_id,
        type="COMMENT",
        content=f"{commenter.username} đã bình luận bài viết của bạn",
        link=f"/posts/{post.id}",
    )

db.commit()
```

**Lưu ý:** Các ví dụ trên là vị trí tích hợp mẫu. Khi đưa vào module thực tế, dùng đúng biến và đối tượng đang có trong module đó. Nếu nghiệp vụ thất bại, rollback transaction để thông báo không bị lưu riêng.

## 4. API Notification

Tất cả API dưới đây yêu cầu JWT access token. Header:

```http
Authorization: Bearer <access_token>
```

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/notifications` | Lấy danh sách thông báo |
| GET | `/notifications/unread-count` | Lấy số thông báo chưa đọc |
| PATCH | `/notifications/{notification_id}/read` | Đánh dấu một thông báo đã đọc |
| PATCH | `/notifications/read-all` | Đánh dấu tất cả thông báo đã đọc |

### 4.1. Danh sách thông báo

```http
GET /notifications?skip=0&limit=20
```

- `skip`: số bản ghi bỏ qua, mặc định `0`.
- `limit`: số bản ghi trả về, mặc định `20`, tối đa `100`.
- Chỉ trả về thông báo của tài khoản đang đăng nhập.
- Sắp xếp mới nhất trước.

### 4.2. Số thông báo chưa đọc

```http
GET /notifications/unread-count
```

Dữ liệu trong `data`:

```json
{
  "unread_count": 3
}
```

### 4.3. Đánh dấu một thông báo đã đọc

```http
PATCH /notifications/12/read
```

Chỉ người nhận thông báo mới được phép đánh dấu đã đọc.

### 4.4. Đánh dấu tất cả đã đọc

```http
PATCH /notifications/read-all
```

Dữ liệu trong `data`:

```json
{
  "updated_count": 3
}
```

## 5. Quy chuẩn response

Các response thành công của Notification sử dụng `api_repoint()` trong `app/schemas/api_response.py`, gồm đúng 6 trường ngoài cùng:

```json
{
  "status_code": 200,
  "message": "Lấy danh sách thông báo thành công",
  "data": [],
  "error": null,
  "timestamp": "2026-11-10T10:00:00",
  "path": "/notifications"
}
```

Không tự tạo format response khác cho các API Notification thành công.

Các lỗi xác thực, không tìm thấy dữ liệu hoặc tham số không hợp lệ hiện dùng `HTTPException`, theo cách xử lý đang có trong dự án.

## 6. Database

Bảng `notifications` được tạo bằng `sql/notifications.sql`. File này đã được gọi trong `sql/run_all.sql`, sau khi bảng `users` được tạo.

Model Notification cũng được import trong `app/models/__init__.py` để SQLAlchemy nhận diện model.
