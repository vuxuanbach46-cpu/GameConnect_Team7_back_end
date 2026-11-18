# API báo cáo vi phạm

## Endpoint

`POST /reports` (yêu cầu đăng nhập, gửi Access Token trong header `Authorization: Bearer <token>`).

Ví dụ request:

```json
{
  "target_type": "POST",
  "target_id": 15,
  "reason": "SPAM",
  "description": "Bài viết đăng quảng cáo lặp lại"
}
```

`target_type` nhận một trong: `USER`, `POST`, `COMMENT`, `TEAM_POST`.

`reason` nhận một trong: `SPAM`, `HARASSMENT`, `HATE_SPEECH`, `INAPPROPRIATE_CONTENT`, `SCAM`, `OTHER`.

`description` không bắt buộc, tối đa 2000 ký tự.

## Quy tắc

- Mỗi tài khoản chỉ báo cáo một đối tượng một lần, áp dụng cho từng loại đối tượng và ID.
- Không thể báo cáo tài khoản của chính mình.
- Đối tượng không tồn tại trả về 404.
- Báo cáo trùng trả về 409.
- Báo cáo mới có trạng thái `PENDING`.
- Response thành công dùng `api_repoint()` với đủ 6 trường.

## Dùng nút Báo cáo chung ở Frontend

Tái sử dụng một modal/form báo cáo ở các trang. Khi mở form, truyền `target_type` và `target_id` của đối tượng hiện tại. Khi người dùng chọn lý do và gửi, gọi `POST /reports` với dữ liệu trên. Ví dụ:

- Trang hồ sơ: `target_type: "USER"`, `target_id: user.id`.
- Trang bài viết: `target_type: "POST"`, `target_id: post.id`.
- Bình luận: `target_type: "COMMENT"`, `target_id: comment.id`.
- Bài tìm đội: `target_type: "TEAM_POST"`, `target_id: teamPost.id`.

Không tạo bốn API riêng cho bốn loại đối tượng.

## Lưu ý database

Với database đã có bảng `reports`, cần bảo đảm có unique key `uq_reports_reporter_target` trên ba cột `(reporter_id, target_type, target_id)`. Nếu bảng đã có dữ liệu trùng theo ba cột này, cần xử lý dữ liệu trùng trước khi thêm unique key.
