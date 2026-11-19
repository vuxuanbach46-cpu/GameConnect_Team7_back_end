# BÁO CÁO KIỂM THỬ TỔNG HỢP (TEST CASES & TEST LOG)

> **Mã Task**: `T3CC6DF`  
> **Dự án**: GameConnect - Gaming Hub (Team 7)  
> **Phân hệ**: Tìm đồng đội, Ứng tuyển & Gợi ý bài đăng (Team Finding & Applications)  
> **Các tính năng phụ trách**:
> - `T3CCE5B`: API ứng tuyển vào bài đăng, duyệt/từ chối ứng viên, tự động chuyển FULL, gửi thông báo.
> - `T3CCE75`: UI Bài của tôi & người ứng tuyển, trang Tôi đã ứng tuyển.
> - `T3CCE98`: API & UI Gợi ý bài đăng theo Game & Rank ở trang chủ.  
> **File Excel đính kèm**: [`docs/TEST_CASES_AND_TEST_LOG_T3CC6DF.xlsx`](TEST_CASES_AND_TEST_LOG_T3CC6DF.xlsx)  
> **Ngày thực hiện**: 19/11/2026  
> **Trạng thái tổng thể**: **PASS 100% (27/27 Test Cases đạt)**

---

## I. DASHBOARD & TỔNG QUAN KIỂM THỬ

### 1. Thống kê chỉ số KPI
| Chỉ số | Kết quả | Ghi chú |
| :--- | :---: | :--- |
| **Tổng số Test Cases** | **27** | Bao phủ đầy đủ các module đảm nhiệm |
| **Số Test Case PASS** | **27** | Đạt 100% |
| **Số Test Case FAIL** | **0** | Không còn lỗi tồn đọng |
| **Tỷ lệ đạt (Pass Rate)** | **100%** | Sẵn sàng đưa vào nhánh `develop` |
| **Tổng số Bug phát hiện & xử lý** | **4 / 4** | Đã sửa dứt điểm 100% |

### 2. Phân bổ độ bao phủ kiểm thử (Test Coverage)
| Nhóm kiểm thử | Số TC | Pass | Fail | Tỷ lệ Đạt | Phạm vi bao phủ |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Đúng dữ liệu (Happy Path)** | 10 | 10 | 0 | 100% | Ứng tuyển thành công, duyệt/từ chối, chuyển FULL, lọc theo rank khớp |
| **2. Sai dữ liệu (Invalid / Boundary)** | 6 | 6 | 0 | 100% | Bài không tồn tại, trạng thái bài đóng/hết hạn, tham số limit âm |
| **3. Chưa đăng nhập (Unauthorized)** | 5 | 5 | 0 | 100% | Thiếu Bearer token, token hết hạn/sai chữ ký, redirect về login |
| **4. Sai quyền (Forbidden / Access Control)**| 3 | 3 | 0 | 100% | Tự ứng tuyển bài của mình, người khác duyệt đơn thay chủ bài |
| **5. Giao diện & Hiển thị (UI/UX)** | 3 | 3 | 0 | 100% | Khối gợi ý Faceit theme trang chủ, danh sách ứng viên, quản lý bài |

---

## II. BẢNG CHI TIẾT TEST CASES

| Mã TC | Phân hệ / Chức năng | Loại kiểm thử | Tiêu đề Test Case | Các bước thực hiện & Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC_APP_01** | Ứng tuyển (`T3CCE5B`) | Đúng dữ liệu | Ứng tuyển hợp lệ kèm lời nhắn | Gửi `POST /api/team-posts/1/apply` kèm token User B, body: `{message: "Cho mình 1 slot đi rừng"}` | Status `200 OK`, tạo record `PENDING`, gửi thông báo cho chủ bài A | Khớp mong đợi. Trả về application_id, notification được tạo | **PASS** |
| **TC_APP_02** | Ứng tuyển (`T3CCE5B`) | Sai quyền | Chủ bài tự ứng tuyển bài mình | Gửi `POST /api/team-posts/1/apply` bằng token User A (chủ bài) | Status `400 Bad Request`, báo "Không thể tự ứng tuyển vào bài đăng của chính mình" | Khớp mong đợi. HTTP 400 | **PASS** |
| **TC_APP_03** | Ứng tuyển (`T3CCE5B`) | Sai quyền | Ứng tuyển trùng lặp | Gửi `POST /api/team-posts/1/apply` lần 2 khi đơn trước đang `PENDING` hoặc `ACCEPTED` | Status `400 Bad Request`, báo "Bạn đã gửi yêu cầu ứng tuyển bài này rồi" | Khớp mong đợi. HTTP 400 | **PASS** |
| **TC_APP_04** | Ứng tuyển (`T3CCE5B`) | Sai dữ liệu | Ứng tuyển vào bài không tồn tại | Gửi `POST /api/team-posts/999999/apply` | Status `404 Not Found`, báo "Không tìm thấy bài đăng" | Khớp mong đợi. HTTP 404 | **PASS** |
| **TC_APP_05** | Ứng tuyển (`T3CCE5B`) | Sai dữ liệu | Ứng tuyển vào bài đã CLOSED/FULL/Hết hạn | Gửi `POST /api/team-posts/2/apply` vào bài có status `CLOSED` | Status `400 Bad Request`, báo "Bài đăng đã đóng hoặc đã đủ người" | Khớp mong đợi. HTTP 400 | **PASS** |
| **TC_APP_06** | Ứng tuyển (`T3CCE5B`) | Chưa đăng nhập | Gửi ứng tuyển không có token | Gửi `POST /api/team-posts/1/apply` không có header `Authorization` | Status `401 Unauthorized` | Khớp mong đợi. HTTP 401 | **PASS** |
| **TC_APP_07** | Ứng tuyển (`T3CCE5B`) | Chưa đăng nhập | Gửi ứng tuyển với token sai/hết hạn | Gửi `POST /api/team-posts/1/apply` kèm `Authorization: Bearer invalid_jwt` | Status `401 Unauthorized`, hỗ trợ đầy đủ CORS header | Khớp mong đợi. HTTP 401 | **PASS** |
| **TC_APP_08** | Duyệt ứng viên (`T3CCE5B`) | Đúng dữ liệu | Chủ bài chấp nhận ứng viên (`ACCEPTED`) | Chủ bài A gửi `PATCH /api/team-posts/1/applications/1`, body: `{status: "ACCEPTED"}` | Status `200 OK`, chuyển trạng thái `ACCEPTED`, gửi thông báo cho ứng viên B | Khớp mong đợi. HTTP 200 | **PASS** |
| **TC_APP_09** | Duyệt ứng viên (`T3CCE5B`) | Đúng dữ liệu | Đủ người bài đăng tự động chuyển FULL | Bài cần 1 người (`needed_players = 1`). Duyệt chấp nhận 1 đơn | Trạng thái bài đăng tự động cập nhật từ `OPEN` $\rightarrow$ `FULL` | Khớp mong đợi. Bài chuyển status `FULL` ngay lập tức | **PASS** |
| **TC_APP_10** | Duyệt ứng viên (`T3CCE5B`) | Đúng dữ liệu | Chủ bài từ chối ứng viên (`REJECTED`) | Chủ bài A gửi `PATCH /api/team-posts/1/applications/2`, body: `{status: "REJECTED"}` | Status `200 OK`, chuyển trạng thái `REJECTED`, gửi thông báo từ chối | Khớp mong đợi. HTTP 200 | **PASS** |
| **TC_APP_11** | Duyệt ứng viên (`T3CCE5B`) | Sai quyền | Người lạ cố duyệt ứng viên của bài khác | User C gửi lệnh `PATCH /api/team-posts/1/applications/1` (bài của User A) | Status `403 Forbidden`, báo "Bạn không có quyền duyệt ứng viên cho bài đăng này" | Khớp mong đợi. HTTP 403 Forbidden | **PASS** |
| **TC_APP_12** | Duyệt ứng viên (`T3CCE5B`) | Sai dữ liệu | Duyệt với trạng thái enum sai | Gửi `PATCH /api/team-posts/1/applications/1` với body: `{status: "INVALID"}` | Status `422 Unprocessable Entity` | Khớp mong đợi. HTTP 422 | **PASS** |
| **TC_APP_13** | Duyệt ứng viên (`T3CCE5B`) | Sai dữ liệu | Application ID không tồn tại | Gửi `PATCH /api/team-posts/1/applications/9999` | Status `404 Not Found` | Khớp mong đợi. HTTP 404 | **PASS** |
| **TC_APP_14** | Duyệt ứng viên (`T3CCE5B`) | Chưa đăng nhập | Duyệt ứng viên khi chưa có token | Gửi `PATCH /api/team-posts/1/applications/1` không có token | Status `401 Unauthorized` | Khớp mong đợi. HTTP 401 | **PASS** |
| **TC_UI_15** | Bài của tôi (`T3CCE75`) | Đúng dữ liệu | Xem danh sách bài đăng & ứng viên | Đăng nhập tài khoản User A, truy cập `pages/my-team-posts.html` | Hiển thị các bài đã đăng, danh sách người nộp đơn (avatar, username, message, status) | Khớp mong đợi. Render chính xác | **PASS** |
| **TC_UI_16** | Bài của tôi (`T3CCE75`) | Đúng dữ liệu | Thao tác Chấp nhận/Từ chối trên UI | Bấm nút "Chấp nhận" trên hàng ứng viên trong modal quản lý | Gọi API thành công, badge chuyển sang "Đã chấp nhận", hiện toast thông báo | Khớp mong đợi. UI cập nhật tức thì | **PASS** |
| **TC_UI_17** | Bài của tôi (`T3CCE75`) | Đúng dữ liệu | Lọc bài đăng theo tab trạng thái | Click các tab `Tất cả`, `Đang mở`, `Đã đủ`, `Đã đóng` | Danh sách bài lọc đúng theo trạng thái tương ứng | Khớp mong đợi. Lọc chính xác | **PASS** |
| **TC_UI_18** | Bài của tôi (`T3CCE75`) | Chưa đăng nhập | Truy cập trang khi chưa đăng nhập | Xoá token khỏi localStorage và mở `pages/my-team-posts.html` | Auth-guard phát hiện và tự động chuyển hướng về `pages/login.html` | Khớp mong đợi. Redirect an toàn | **PASS** |
| **TC_UI_19** | Tôi đã ứng tuyển (`T3CCE75`) | Đúng dữ liệu | Xem các bài đăng mình đã nộp đơn | User B truy cập `pages/my-team-posts.html?tab=applied` | Hiển thị danh sách các bài đã nộp kèm trạng thái đơn (Chờ duyệt / Đã nhận / Từ chối) | Khớp mong đợi. Hiển thị đầy đủ thông tin | **PASS** |
| **TC_UI_20** | Tôi đã ứng tuyển (`T3CCE75`) | Sai dữ liệu | Phân trang vượt quá giới hạn trang | Gọi `GET /api/team-posts/my-applications?page=9999` | Trả về mảng rỗng `[]`, không gây lỗi server 500, UI báo trạng thái rỗng | Khớp mong đợi. Xử lý an toàn | **PASS** |
| **TC_REC_21** | Gợi ý bài đăng (`T3CCE98`) | Đúng dữ liệu | Gợi ý khớp game & rank trong hồ sơ | User có game LoL rank Platinum (3), bài đăng tuyển rank Gold (2) -> Diamond (4) | Gợi ý bài đăng lên đầu kèm huy hiệu `Phù hợp: Rank Platinum` | Khớp mong đợi. So khớp rank chuẩn xác | **PASS** |
| **TC_REC_22** | Gợi ý bài đăng (`T3CCE98`) | Đúng dữ liệu | Loại trừ bài đăng có rank không phù hợp | User rank Platinum (3), bài đăng tuyển rank Iron (0) -> Silver (1) | Bài không được đánh dấu là bài phù hợp của user | Khớp mong đợi. Lọc chuẩn xác | **PASS** |
| **TC_REC_23** | Gợi ý bài đăng (`T3CCE98`) | Sai quyền | Không tự gợi ý bài do chính mình tạo | User A gọi API gợi ý | Bài đăng của User A không bao giờ xuất hiện trong gợi ý cho chính User A | Khớp mong đợi. `user_id != current_user.id` | **PASS** |
| **TC_REC_24** | Gợi ý bài đăng (`T3CCE98`) | Đúng dữ liệu | Loại trừ bài đã CLOSED, FULL hoặc hết hạn | Bài đăng khớp rank nhưng đã `CLOSED` hoặc quá hạn `expires_at` | Bị loại bỏ khỏi danh sách gợi ý | Khớp mong đợi. Chỉ lấy bài OPEN còn hạn | **PASS** |
| **TC_REC_25** | Gợi ý bài đăng (`T3CCE98`) | Chưa đăng nhập | Khách vãng lai xem trang chủ | Không gửi header Authorization khi gọi `GET /api/team-posts/recommendations` | Status `200 OK`, trả về các bài đăng `OPEN` mới nhất làm fallback | Khớp mong đợi. Trang chủ không bị crash | **PASS** |
| **TC_REC_26** | Gợi ý bài đăng (`T3CCE98`) | Đúng dữ liệu | User chưa cập nhật game trong hồ sơ | User đã đăng nhập nhưng chưa có bản ghi trong bảng `user_games` | Trả về `has_profile_games: false`, fallback bài mở, UI hiển thị banner nhắc cập nhật | Khớp mong đợi. Hiển thị thân thiện | **PASS** |
| **TC_REC_27** | Gợi ý bài đăng (`T3CCE98`) | Sai dữ liệu | Tham số limit gửi số âm hoặc sai định dạng | Gọi `GET /api/team-posts/recommendations?limit=-5` | Status `422 Unprocessable Entity` rõ ràng | Khớp mong đợi. HTTP 422 | **PASS** |

---

## III. NHẬT KÝ KIỂM THỬ & BUG LOG (DEFECT REPORT)

| Mã Bug | Phân hệ | Liên quan TC | Mô tả lỗi phát hiện | Mức độ | Nguyên nhân gốc rễ | Giải pháp khắc phục | Trạng thái | Kết quả Retest |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :---: | :---: |
| **BUG-01** | Backend Test | `TC_REC_21` | Lỗi `IntegrityError: NOT NULL constraint failed: games.genre` trong unit test | High | Model `Game` quy định trường `genre` là NOT NULL, nhưng fixture test chưa điền `genre`. | Cập nhật fixture: `Game(name='LoL', genre='MOBA')` và `Game(name='Valorant', genre='FPS')`. | **ĐÃ SỬA (CLOSED)** | **PASS** |
| **BUG-02** | Security / Auth | `TC_APP_07` | Khi gửi token sai/hết hạn, backend trả 401 nhưng bị lỗi CORS trên trình duyệt | High | `AuthMiddleware` đặt sau `CORSMiddleware` và trả response trực tiếp khi bắt ngoại lệ JWT, khiến CORS headers không được gắn vào response 401. | Chuyển `AuthMiddleware` lên trước và gắn header CORS trực tiếp trong hàm `_auth_error`. | **ĐÃ SỬA (CLOSED)** | **PASS** |
| **BUG-03** | Router API | `TC_REC_25` | Gọi API `/team-posts/recommendations` bị 404 do router đăng ký với tiền tố `/api` | Medium | Frontend một số nơi gọi `/api/team-posts` và một số nơi gọi `/team-posts`. | Đăng ký router ở cả 2 tiền tố và hỗ trợ đồng thời cả endpoint `/recommendations` và `/recommended`. | **ĐÃ SỬA (CLOSED)** | **PASS** |
| **BUG-04** | Frontend Home | `TC_UI_15` | Trang `home.html` ban đầu chưa import thư viện `axios`, `config.js`, `api.js`, `utils.js` | Medium | Thiếu các script dùng chung trước `home.js` khiến trang không gọi được API và hàm an toàn `escapeHtml`. | Bổ sung đầy đủ thẻ script thư viện vào cuối file `pages/home.html`. | **ĐÃ SỬA (CLOSED)** | **PASS** |

---

## IV. HƯỚNG DẪN MỞ & XUẤT FILE EXCEL
* File Excel chuẩn đã được tạo tự động tại đường dẫn: [`docs/TEST_CASES_AND_TEST_LOG_T3CC6DF.xlsx`](TEST_CASES_AND_TEST_LOG_T3CC6DF.xlsx)
* File bao gồm 3 Sheet:
  1. **Dashboard & Tổng quan**: Các thẻ KPI, tỷ lệ đạt 100%, bảng phân bổ Test Coverage.
  2. **Chi tiết Test Cases**: Toàn bộ 27 test cases phân loại theo Đúng dữ liệu, Sai dữ liệu, Chưa đăng nhập, Sai quyền.
  3. **Test Log & Bug Report**: Chi tiết 4 bug phát hiện và tình trạng đã xử lý dứt điểm.
* Có thể mở trực tiếp bằng **Microsoft Excel**, **WPS Office** hoặc import nhanh lên **Google Sheets**.
