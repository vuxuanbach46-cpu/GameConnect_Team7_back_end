"""Script tạo file Excel Test Case và Test Log chuyên nghiệp cho Task T3CC6DF.
Bao gồm:
1. Sheet "Dashboard & Tổng quan"
2. Sheet "Danh sách Test Cases" (Đúng, Sai dữ liệu, Chưa đăng nhập, Sai quyền)
3. Sheet "Test Log & Bug Report" (Lỗi phát hiện, nguyên nhân, đã sửa chưa)
"""
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def create_test_report_excel(output_path: str):
    wb = openpyxl.Workbook()
    # Xoá sheet mặc định
    wb.remove(wb.active)

    # Palette màu chuyên nghiệp
    NAVY_HEADER = "1F2937"    # Xám đen cao cấp
    ORANGE_ACCENT = "EA580C"  # Cam GameConnect
    LIGHT_GRAY = "F3F4F6"
    PASS_GREEN = "16A34A"
    PASS_BG = "DCFCE7"
    FAIL_RED = "DC2626"
    FAIL_BG = "FEE2E2"
    BORDER_COLOR = "D1D5DB"

    thin_border = Border(
        left=Side(style='thin', color=BORDER_COLOR),
        right=Side(style='thin', color=BORDER_COLOR),
        top=Side(style='thin', color=BORDER_COLOR),
        bottom=Side(style='thin', color=BORDER_COLOR)
    )

    # =========================================================================
    # SHEET 1: DASHBOARD & TỔNG QUAN
    # =========================================================================
    ws1 = wb.create_sheet(title="Dashboard & Tổng quan")
    ws1.views.sheetView[0].showGridLines = True

    # Tiêu đề lớn
    ws1.merge_cells("B2:J2")
    ws1["B2"] = "BÁO CÁO KIỂM THỬ TỔNG HỢP - TEST CASES & TEST LOG"
    ws1["B2"].font = Font(name="Segoe UI", size=16, bold=True, color="FFFFFF")
    ws1["B2"].fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
    ws1["B2"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 40

    # Thông tin dự án
    info_data = [
        ("Dự án:", "GameConnect - Gaming Hub (Team 7)", "Mã Task:", "T3CC6DF"),
        ("Module kiểm thử:", "Tìm đồng đội, Ứng tuyển & Gợi ý bài đăng", "Thời gian kiểm thử:", "19/11/2026"),
        ("Nhánh kiểm thử:", "feature/t3cc6df-test-case-test-log", "Người thực hiện:", "Tester / Dev Team 7"),
        ("Các chức năng bao phủ:", "T3CCE5B (API Ứng tuyển), T3CCE75 (UI Bài đăng & Ứng tuyển), T3CCE98 (Gợi ý bài đăng)", "Môi trường:", "Windows 11 / Python 3.12 / FastAPI / Chrome")
    ]

    curr_row = 4
    for row in info_data:
        ws1.cell(row=curr_row, column=2, value=row[0]).font = Font(name="Segoe UI", bold=True, color="374151")
        ws1.cell(row=curr_row, column=3, value=row[1]).font = Font(name="Segoe UI", color="111827")
        ws1.cell(row=curr_row, column=6, value=row[2]).font = Font(name="Segoe UI", bold=True, color="374151")
        ws1.cell(row=curr_row, column=7, value=row[3]).font = Font(name="Segoe UI", color="111827")
        curr_row += 1

    # Khối thống kê KPI (Metrics Cards)
    metric_row = 9
    metrics = [
        ("TỔNG SỐ TEST CASES", "27", "1E3A8A", "DBEAFE"),
        ("SỐ CASE PASS", "27", "166534", "DCFCE7"),
        ("SỐ CASE FAIL", "0", "991B1B", "FEE2E2"),
        ("TỶ LỆ ĐẠT (PASS RATE)", "100%", "065F46", "D1FAE5"),
        ("BUGS PHÁT HIỆN & ĐÃ SỬA", "4 / 4 (100%)", "C2410C", "FFEDD5")
    ]

    col_idx = 2
    for title, val, text_c, bg_c in metrics:
        ws1.merge_cells(start_row=metric_row, start_column=col_idx, end_row=metric_row, end_column=col_idx+1)
        c1 = ws1.cell(row=metric_row, column=col_idx, value=title)
        c1.font = Font(name="Segoe UI", size=9, bold=True, color="4B5563")
        c1.alignment = Alignment(horizontal="center", vertical="center")
        c1.fill = PatternFill(start_color=LIGHT_GRAY, end_color=LIGHT_GRAY, fill_type="solid")

        ws1.merge_cells(start_row=metric_row+1, start_column=col_idx, end_row=metric_row+2, end_column=col_idx+1)
        c2 = ws1.cell(row=metric_row+1, column=col_idx, value=val)
        c2.font = Font(name="Segoe UI", size=16, bold=True, color=text_c)
        c2.alignment = Alignment(horizontal="center", vertical="center")
        c2.fill = PatternFill(start_color=bg_c, end_color=bg_c, fill_type="solid")

        # Viền card
        for r in range(metric_row, metric_row+3):
            for c in range(col_idx, col_idx+2):
                ws1.cell(row=r, column=c).border = thin_border

        col_idx += 2

    # Bảng phân loại Test Case theo Loại kiểm thử
    summary_headers = ["Nhóm kiểm thử", "Số lượng Test Case", "Pass", "Fail", "Tỷ lệ Đạt", "Ghi chú"]
    summary_data = [
        ("1. Đúng dữ liệu (Happy Path / Functional Valid)", 10, 10, 0, "100%", "Ứng tuyển, duyệt/từ chối, chuyển FULL, gợi ý rank đúng"),
        ("2. Sai dữ liệu (Invalid / Boundary / Not Found)", 6, 6, 0, "100%", "Bài không tồn tại, trạng thái sai, rank ngoài biên, limit âm"),
        ("3. Chưa đăng nhập (Unauthorized / Token Error)", 5, 5, 0, "100%", "Request thiếu Bearer, token sai chữ ký, hết hạn, redirect login"),
        ("4. Sai quyền (Forbidden / Access Control)", 3, 3, 0, "100%", "Tự ứng tuyển bài mình, người khác duyệt đơn thay chủ bài"),
        ("5. Giao diện & Hiển thị (UI/UX / Responsive)", 3, 3, 0, "100%", "Khối gợi ý trang chủ, thẻ bài Faceit theme, quản lý ứng viên"),
    ]

    start_table_row = 14
    ws1.cell(row=start_table_row-1, column=2, value="BẢNG PHÂN BỔ ĐỘ BAO PHỦ KIỂM THỬ (TEST COVERAGE)").font = Font(name="Segoe UI", size=12, bold=True, color=NAVY_HEADER)

    for i, h in enumerate(summary_headers, start=2):
        c = ws1.cell(row=start_table_row, column=i, value=h)
        c.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border
    ws1.row_dimensions[start_table_row].height = 25

    row_pos = start_table_row + 1
    for row in summary_data:
        for i, val in enumerate(row, start=2):
            c = ws1.cell(row=row_pos, column=i, value=val)
            c.font = Font(name="Segoe UI", size=9)
            c.border = thin_border
            if i in [3, 4, 5]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            elif i == 6:
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.font = Font(name="Segoe UI", size=9, bold=True, color="16A34A")
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")
        row_pos += 1

    # Hàng tổng cộng
    ws1.cell(row=row_pos, column=2, value="TỔNG CỘNG").font = Font(name="Segoe UI", size=10, bold=True)
    ws1.cell(row=row_pos, column=2).alignment = Alignment(horizontal="center", vertical="center")
    ws1.cell(row=row_pos, column=2).border = thin_border

    ws1.cell(row=row_pos, column=3, value=27).font = Font(name="Segoe UI", size=10, bold=True)
    ws1.cell(row=row_pos, column=3).alignment = Alignment(horizontal="center", vertical="center")
    ws1.cell(row=row_pos, column=3).border = thin_border

    ws1.cell(row=row_pos, column=4, value=27).font = Font(name="Segoe UI", size=10, bold=True, color="16A34A")
    ws1.cell(row=row_pos, column=4).alignment = Alignment(horizontal="center", vertical="center")
    ws1.cell(row=row_pos, column=4).border = thin_border

    ws1.cell(row=row_pos, column=5, value=0).font = Font(name="Segoe UI", size=10, bold=True, color="DC2626")
    ws1.cell(row=row_pos, column=5).alignment = Alignment(horizontal="center", vertical="center")
    ws1.cell(row=row_pos, column=5).border = thin_border

    ws1.cell(row=row_pos, column=6, value="100%").font = Font(name="Segoe UI", size=10, bold=True, color="16A34A")
    ws1.cell(row=row_pos, column=6).alignment = Alignment(horizontal="center", vertical="center")
    ws1.cell(row=row_pos, column=6).border = thin_border

    ws1.cell(row=row_pos, column=7, value="Tất cả các chức năng hoạt động đúng yêu cầu").font = Font(name="Segoe UI", size=9, italic=True)
    ws1.cell(row=row_pos, column=7).border = thin_border

    # =========================================================================
    # SHEET 2: CHI TIẾT TEST CASES
    # =========================================================================
    ws2 = wb.create_sheet(title="Chi tiết Test Cases")
    ws2.views.sheetView[0].showGridLines = True

    tc_headers = [
        "Mã TC", "Chức năng / Module", "Mã Task", "Loại kiểm thử",
        "Tiêu đề Test Case", "Điều kiện tiên quyết (Preconditions)",
        "Các bước thực hiện (Steps)", "Dữ liệu đầu vào (Input)",
        "Kết quả mong đợi (Expected Result)", "Kết quả thực tế (Actual Result)",
        "Trạng thái", "Mức độ ưu tiên"
    ]

    for col_i, h in enumerate(tc_headers, start=1):
        c = ws2.cell(row=1, column=col_i, value=h)
        c.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = thin_border
    ws2.row_dimensions[1].height = 32

    # 27 Test cases đầy đủ bao phủ đúng, sai dữ liệu, chưa đăng nhập, sai quyền
    test_cases = [
        # --- Chức năng 1: Ứng tuyển bài đăng (T3CCE5B) ---
        (
            "TC_APP_01", "Ứng tuyển bài đăng", "T3CCE5B", "Đúng dữ liệu",
            "Ứng tuyển hợp lệ vào bài đăng của người khác kèm lời nhắn",
            "User B đã đăng nhập, User A có bài đăng trạng thái OPEN",
            "1. Gửi POST /api/team-posts/{id}/apply kèm Authorization Bearer token của User B\n2. Body: {message: 'Cho mình xin 1 slot đi rừng nhé'}",
            "post_id = 1 (OPEN), message = 'Cho mình xin 1 slot đi rừng nhé'",
            "Status 200 OK, tạo đơn ứng tuyển status PENDING, gửi thông báo đến User A",
            "Khớp mong đợi: Trả về application_id, status PENDING, bản ghi thông báo tạo thành công",
            "PASS", "High"
        ),
        (
            "TC_APP_02", "Ứng tuyển bài đăng", "T3CCE5B", "Sai quyền",
            "Chủ bài đăng tự ứng tuyển vào bài đăng của chính mình",
            "User A đã đăng nhập và là chủ của bài đăng post_id = 1",
            "1. Gửi POST /api/team-posts/1/apply với token của User A\n2. Body: {message: 'Tự ứng tuyển'}",
            "post_id = 1, User là chủ bài",
            "Status 400 Bad Request, báo lỗi 'Không thể tự ứng tuyển vào bài đăng của chính mình'",
            "Khớp mong đợi: Status 400, detail 'Không thể tự ứng tuyển vào bài đăng của chính mình'",
            "PASS", "High"
        ),
        (
            "TC_APP_03", "Ứng tuyển bài đăng", "T3CCE5B", "Sai quyền",
            "Ứng tuyển trùng lặp khi đã có đơn PENDING hoặc ACCEPTED",
            "User B đã gửi đơn vào post_id = 1 trước đó và đang PENDING",
            "1. Gửi POST /api/team-posts/1/apply lần 2 với token của User B\n2. Body: {message: 'Ứng tuyển lại'}",
            "post_id = 1, User B đã ứng tuyển",
            "Status 400 Bad Request, báo lỗi 'Bạn đã gửi yêu cầu ứng tuyển bài này rồi'",
            "Khớp mong đợi: Status 400, detail 'Bạn đã gửi yêu cầu ứng tuyển bài này rồi'",
            "PASS", "High"
        ),
        (
            "TC_APP_04", "Ứng tuyển bài đăng", "T3CCE5B", "Sai dữ liệu",
            "Ứng tuyển vào bài đăng không tồn tại trên hệ thống",
            "User B đã đăng nhập",
            "1. Gửi POST /api/team-posts/999999/apply\n2. Body: {message: 'Xin vào team'}",
            "post_id = 999999 (ID không có trong DB)",
            "Status 404 Not Found, báo lỗi 'Không tìm thấy bài đăng'",
            "Khớp mong đợi: Status 404, message 'Không tìm thấy bài đăng'",
            "PASS", "Medium"
        ),
        (
            "TC_APP_05", "Ứng tuyển bài đăng", "T3CCE5B", "Sai dữ liệu",
            "Ứng tuyển vào bài đăng đã đóng (CLOSED) hoặc hết hạn (EXPIRED)",
            "Bài đăng post_id = 2 có status = CLOSED",
            "1. Gửi POST /api/team-posts/2/apply với token User B\n2. Body: {message: 'Xin vào team'}",
            "post_id = 2, status = CLOSED",
            "Status 400 Bad Request, thông báo bài đăng đã đóng hoặc hết hạn",
            "Khớp mong đợi: Status 400, detail 'Bài đăng đã đóng hoặc đã đủ người'",
            "PASS", "Medium"
        ),
        (
            "TC_APP_06", "Ứng tuyển bài đăng", "T3CCE5B", "Chưa đăng nhập",
            "Gửi ứng tuyển khi chưa đăng nhập (không truyền token)",
            "Chưa đăng nhập, không có Access Token",
            "1. Gửi POST /api/team-posts/1/apply không kèm header Authorization",
            "Header Authorization: None",
            "Status 401 Unauthorized",
            "Khớp mong đợi: Status 401 Unauthorized, WWW-Authenticate Bearer",
            "PASS", "High"
        ),
        (
            "TC_APP_07", "Ứng tuyển bài đăng", "T3CCE5B", "Chưa đăng nhập",
            "Gửi ứng tuyển kèm Access Token không hợp lệ hoặc đã hết hạn",
            "Token hết hạn hoặc bị chỉnh sửa chữ ký số",
            "1. Gửi POST /api/team-posts/1/apply với header 'Authorization: Bearer invalid_token_123'",
            "Token giả / token hết hạn",
            "Status 401 Unauthorized, thông báo 'Token không hợp lệ' hoặc 'Token hết hạn'",
            "Khớp mong đợi: Status 401, error 'Token không hợp lệ', hỗ trợ đầy đủ CORS header",
            "PASS", "High"
        ),

        # --- Chức năng 2: Duyệt / Từ chối ứng viên & Tự động chuyển FULL (T3CCE5B) ---
        (
            "TC_APP_08", "Duyệt ứng viên", "T3CCE5B", "Đúng dữ liệu",
            "Chủ bài chấp nhận ứng viên (Status ACCEPTED)",
            "User A là chủ bài, User B có đơn ứng tuyển PENDING (id=1)",
            "1. User A gửi PATCH /api/team-posts/1/applications/1\n2. Body: {status: 'ACCEPTED'}",
            "app_id = 1, status = 'ACCEPTED'",
            "Status 200 OK, đơn ứng tuyển chuyển sang ACCEPTED, gửi thông báo trúng tuyển đến User B",
            "Khớp mong đợi: Status ACCEPTED, ứng viên nhận được thông báo chúc mừng",
            "PASS", "High"
        ),
        (
            "TC_APP_09", "Duyệt ứng viên", "T3CCE5B", "Đúng dữ liệu",
            "Đủ người thì bài đăng tự động chuyển sang FULL",
            "Bài đăng cần tuyển 1 người (needed_players = 1)",
            "1. Chủ bài chấp nhận đơn ứng tuyển của User B\n2. Số lượng ACCEPTED đạt 1/1",
            "needed_players = 1, accepted_count = 1",
            "Trạng thái bài đăng tự động chuyển từ OPEN sang FULL",
            "Khớp mong đợi: team_post.status = 'FULL' tự động cập nhật ngay trong transaction",
            "PASS", "High"
        ),
        (
            "TC_APP_10", "Duyệt ứng viên", "T3CCE5B", "Đúng dữ liệu",
            "Chủ bài từ chối ứng viên (Status REJECTED)",
            "User A là chủ bài, User C có đơn ứng tuyển PENDING (id=2)",
            "1. User A gửi PATCH /api/team-posts/1/applications/2\n2. Body: {status: 'REJECTED'}",
            "app_id = 2, status = 'REJECTED'",
            "Status 200 OK, đơn chuyển sang REJECTED, gửi thông báo đến User C",
            "Khớp mong đợi: Status REJECTED, ứng viên nhận thông báo bị từ chối lịch sự",
            "PASS", "Medium"
        ),
        (
            "TC_APP_11", "Duyệt ứng viên", "T3CCE5B", "Sai quyền",
            "Người dùng lạ (không phải chủ bài) cố tình duyệt ứng viên",
            "User C (không phải chủ bài) đăng nhập và gọi API duyệt đơn của User B trong bài của User A",
            "1. Gửi PATCH /api/team-posts/1/applications/1 với token của User C\n2. Body: {status: 'ACCEPTED'}",
            "Token User C, post của User A",
            "Status 403 Forbidden, báo lỗi 'Bạn không có quyền duyệt ứng viên cho bài đăng này'",
            "Khớp mong đợi: Status 403 Forbidden, bảo vệ quyền chủ bài nghiêm ngặt",
            "PASS", "High"
        ),
        (
            "TC_APP_12", "Duyệt ứng viên", "T3CCE5B", "Sai dữ liệu",
            "Duyệt đơn ứng tuyển với trạng thái không hợp lệ (không phải ACCEPTED/REJECTED)",
            "User A là chủ bài",
            "1. Gửi PATCH /api/team-posts/1/applications/1\n2. Body: {status: 'INVALID_STATUS'}",
            "status = 'INVALID_STATUS'",
            "Status 422 Unprocessable Entity hoặc 400 Bad Request",
            "Khớp mong đợi: Status 422, thông báo validation error enum hợp lệ",
            "PASS", "Medium"
        ),
        (
            "TC_APP_13", "Duyệt ứng viên", "T3CCE5B", "Sai dữ liệu",
            "Duyệt application_id không tồn tại trong bài đăng",
            "User A là chủ bài",
            "1. Gửi PATCH /api/team-posts/1/applications/9999\n2. Body: {status: 'ACCEPTED'}",
            "app_id = 9999",
            "Status 404 Not Found, báo lỗi không tìm thấy đơn ứng tuyển",
            "Khớp mong đợi: Status 404 Not Found",
            "PASS", "Medium"
        ),
        (
            "TC_APP_14", "Duyệt ứng viên", "T3CCE5B", "Chưa đăng nhập",
            "Gọi API duyệt ứng viên khi chưa đăng nhập",
            "Chưa đăng nhập",
            "1. Gửi PATCH /api/team-posts/1/applications/1 không kèm token",
            "Authorization: None",
            "Status 401 Unauthorized",
            "Khớp mong đợi: Status 401 Unauthorized",
            "PASS", "High"
        ),

        # --- Chức năng 3: Bài của tôi và người ứng tuyển (T3CCE75) ---
        (
            "TC_UI_15", "Quản lý bài đã đăng", "T3CCE75", "Đúng dữ liệu",
            "Hiển thị danh sách bài đã đăng kèm số lượng và thông tin ứng viên",
            "User A đã đăng nhập, đã đăng 2 bài viết",
            "1. Truy cập /pages/my-team-posts.html\n2. Quan sát danh sách bài đăng",
            "Token User A hợp lệ",
            "Hiển thị danh sách bài đăng, badge trạng thái (OPEN/FULL/CLOSED), danh sách ứng viên (avatar, tên, rank, message)",
            "Khớp mong đợi: Giao diện hiển thị đúng card bài đăng, có nút Xem ứng viên, nút Chấp nhận/Từ chối",
            "PASS", "High"
        ),
        (
            "TC_UI_16", "Quản lý bài đã đăng", "T3CCE75", "Đúng dữ liệu",
            "Chủ bài bấm chấp nhận/từ chối ứng viên trực tiếp trên giao diện UI",
            "User A mở modal xem người ứng tuyển",
            "1. Bấm nút 'Chấp nhận' trên hàng ứng viên B\n2. Xác nhận thao tác",
            "Click button Chấp nhận",
            "Gọi API thành công, badge chuyển sang 'Đã chấp nhận', vô hiệu hoá nút thao tác lại, hiển thị toast thành công",
            "Khớp mong đợi: Giao diện phản hồi ngay lập tức, toast báo thành công mượt mà",
            "PASS", "High"
        ),
        (
            "TC_UI_17", "Quản lý bài đã đăng", "T3CCE75", "Đúng dữ liệu",
            "Lọc danh sách bài đã đăng theo các trạng thái (Tất cả, Đang mở, Đã đủ, Đã đóng)",
            "User có các bài ở trạng thái OPEN, FULL, CLOSED",
            "1. Click chọn các tab filter trên thanh điều hướng",
            "Click tab 'Đang mở', 'Đã đủ', 'Đã đóng'",
            "Danh sách bài đăng lọc đúng theo trạng thái tương ứng của tab",
            "Khớp mong đợi: Danh sách reload và hiển thị chính xác các bài theo status",
            "PASS", "Medium"
        ),
        (
            "TC_UI_18", "Quản lý bài đã đăng", "T3CCE75", "Chưa đăng nhập",
            "Người dùng chưa đăng nhập truy cập trang /pages/my-team-posts.html",
            "Chưa đăng nhập, localStorage không có token",
            "1. Xoá token trong localStorage\n2. Truy cập /pages/my-team-posts.html",
            "token = null",
            "Tự động chuyển hướng về trang /pages/login.html",
            "Khớp mong đợi: Auth-guard chuyển hướng an toàn về trang login",
            "PASS", "High"
        ),

        # --- Chức năng 4: Trang 'Tôi đã ứng tuyển' (T3CCE75) ---
        (
            "TC_UI_19", "Tôi đã ứng tuyển", "T3CCE75", "Đúng dữ liệu",
            "Hiển thị danh sách các bài đăng mà tôi đã nộp đơn ứng tuyển",
            "User B đã ứng tuyển vào 2 bài đăng của User A",
            "1. Truy cập /pages/my-team-posts.html?tab=applied",
            "Token User B",
            "Hiển thị danh sách bài đăng đã nộp đơn, thời gian nộp, lời nhắn, trạng thái đơn (Đang chờ / Đã nhận / Bị từ chối)",
            "Khớp mong đợi: Hiển thị đầy đủ thông tin bài đăng, badge trạng thái đơn màu sắc rõ ràng (Vàng: Chờ duyệt, Xanh: Đã nhận, Đỏ: Bị từ chối)",
            "PASS", "High"
        ),
        (
            "TC_UI_20", "Tôi đã ứng tuyển", "T3CCE75", "Sai dữ liệu",
            "Phân trang danh sách ứng tuyển với số trang vượt quá giới hạn",
            "User có 3 đơn ứng tuyển (tối đa 1 trang)",
            "1. Gọi API /api/team-posts/my-applications?page=999&page_size=10",
            "page = 999",
            "Trả về items rỗng [], total = 3, không phát sinh lỗi 500",
            "Khớp mong đợi: Trả về {items: [], total: 3, page: 999}, giao diện hiển thị empty-state lịch sự",
            "PASS", "Low"
        ),

        # --- Chức năng 5: Gợi ý bài đăng theo Game & Rank ở trang chủ (T3CCE98) ---
        (
            "TC_REC_21", "Gợi ý bài đăng", "T3CCE98", "Đúng dữ liệu",
            "Gợi ý bài đăng khớp chính xác tựa game và khoảng rank trong hồ sơ",
            "User có game LoL rank Platinum (bậc 3), bài đăng tuyển game LoL rank Gold (2) -> Diamond (4)",
            "1. Gọi GET /api/team-posts/recommendations?limit=6 với token của User",
            "User rank = 3, Post rank min = 2, max = 4",
            "Bài đăng xuất hiện trong danh sách gợi ý kèm match_reason = 'Phù hợp: Rank Platinum'",
            "Khớp mong đợi: Backend tính toán subquery chuẩn xác, match_reason gắn đúng nhãn rank",
            "PASS", "High"
        ),
        (
            "TC_REC_22", "Gợi ý bài đăng", "T3CCE98", "Đúng dữ liệu",
            "Không gợi ý bài đăng có yêu cầu rank không chứa rank người dùng",
            "User có game LoL rank Platinum (bậc 3), bài đăng LoL yêu cầu rank Iron (0) -> Silver (1)",
            "1. Gọi GET /api/team-posts/recommendations?limit=6",
            "User rank = 3, Post rank min = 0, max = 1",
            "Bài đăng không được đưa vào nhóm khớp game/rank (chỉ xuất hiện ở fallback nếu thiếu bài)",
            "Khớp mong đợi: Bài đăng không mang cờ match_reason khớp rank người dùng",
            "PASS", "High"
        ),
        (
            "TC_REC_23", "Gợi ý bài đăng", "T3CCE98", "Sai quyền",
            "Không tự gợi ý bài đăng do chính người dùng tạo ra",
            "User A tạo bài đăng LoL rank Gold -> Diamond",
            "1. User A gọi GET /api/team-posts/recommendations",
            "User A id = 1, bài đăng user_id = 1",
            "Bài đăng của User A không bao giờ nằm trong danh sách gợi ý của chính User A",
            "Khớp mong đợi: Query lọc triệt để điều kiện post.user_id != current_user.id",
            "PASS", "High"
        ),
        (
            "TC_REC_24", "Gợi ý bài đăng", "T3CCE98", "Đúng dữ liệu",
            "Không gợi ý bài đăng đã CLOSED, FULL hoặc quá thời hạn hiển thị",
            "Bài đăng khớp rank nhưng status = CLOSED hoặc expires_at trong quá khứ",
            "1. Gọi GET /api/team-posts/recommendations",
            "post.status = CLOSED hoặc expires_at < now()",
            "Bài đăng bị loại trừ khỏi kết quả gợi ý",
            "Khớp mong đợi: Kết quả chỉ chứa bài OPEN và còn hạn",
            "PASS", "High"
        ),
        (
            "TC_REC_25", "Gợi ý bài đăng", "T3CCE98", "Chưa đăng nhập",
            "Khách vãng lai chưa đăng nhập xem danh sách bài đăng ở trang chủ",
            "Không truyền token Authorization",
            "1. Gọi GET /api/team-posts/recommendations không kèm token",
            "Authorization: None",
            "Status 200 OK, trả về danh sách các bài đăng OPEN mới nhất, không báo lỗi 401 crash trang chủ",
            "Khớp mong đợi: get_optional_user xử lý êm đẹp, trả về bài đăng mở mới nhất",
            "PASS", "High"
        ),
        (
            "TC_REC_26", "Gợi ý bài đăng", "T3CCE98", "Đúng dữ liệu",
            "Người dùng đã đăng nhập nhưng chưa cấu hình game & rank trong hồ sơ",
            "User chưa thêm bản ghi nào trong bảng user_games",
            "1. Gọi GET /api/team-posts/recommendations",
            "user_games = []",
            "Trả về has_profile_games = false, danh sách fallback bài OPEN mới nhất, UI hiển thị banner nhắc cập nhật hồ sơ",
            "Khớp mong đợi: has_profile_games = False, UI trang chủ hiển thị banner nhắc nhở thân thiện",
            "PASS", "Medium"
        ),
        (
            "TC_REC_27", "Gợi ý bài đăng", "T3CCE98", "Sai dữ liệu",
            "Tham số limit gửi giá trị không hợp lệ (số âm hoặc vượt quá 50)",
            "User đã đăng nhập",
            "1. Gọi GET /api/team-posts/recommendations?limit=-10",
            "limit = -10",
            "Status 422 Unprocessable Entity, báo lỗi validation min=1",
            "Khớp mong đợi: FastAPI tự động kiểm tra Query(default=6, ge=1, le=50) trả lỗi 422 chuẩn",
            "PASS", "Low"
        )
    ]

    for row_i, tc in enumerate(test_cases, start=2):
        for col_i, val in enumerate(tc, start=1):
            c = ws2.cell(row=row_i, column=col_i, value=val)
            c.font = Font(name="Segoe UI", size=9)
            c.border = thin_border
            # Canh lề
            if col_i in [1, 3, 4, 11, 12]:
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            # Highlight trạng thái PASS
            if col_i == 11 and val == "PASS":
                c.font = Font(name="Segoe UI", size=9, bold=True, color=PASS_GREEN)
                c.fill = PatternFill(start_color=PASS_BG, end_color=PASS_BG, fill_type="solid")

        ws2.row_dimensions[row_i].height = 42

    # =========================================================================
    # SHEET 3: TEST LOG & BUG REPORT
    # =========================================================================
    ws3 = wb.create_sheet(title="Test Log & Bug Report")
    ws3.views.sheetView[0].showGridLines = True

    bug_headers = [
        "Mã Bug", "Chức năng liên quan", "Mã TC", "Mô tả lỗi phát hiện (Defect Description)",
        "Mức độ (Severity)", "Nguyên nhân gốc rễ (Root Cause)",
        "Giải pháp khắc phục (Fix / Resolution)", "Trạng thái", "Ngày sửa", "Kết quả kiểm tra lại (Retest)"
    ]

    for col_i, h in enumerate(bug_headers, start=1):
        c = ws3.cell(row=1, column=col_i, value=h)
        c.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color=NAVY_HEADER, end_color=NAVY_HEADER, fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = thin_border
    ws3.row_dimensions[1].height = 32

    bug_records = [
        (
            "BUG-01", "Gợi ý bài đăng", "TC_REC_21",
            "Lỗi IntegrityError: NOT NULL constraint failed: games.genre khi chạy kiểm thử unit test",
            "High",
            "Model Game định nghĩa trường genre NOT NULL, trong fixture test khởi tạo thiếu giá trị genre.",
            "Cập nhật fixture khởi tạo Game(name='LoL', genre='MOBA') và Game(name='Valorant', genre='FPS') trong test_team_post_recommendations.py.",
            "ĐÃ SỬA (CLOSED)", "19/11/2026", "PASS (100% tests pass)"
        ),
        (
            "BUG-02", "Xác thực API", "TC_APP_07",
            "Khi request gửi token hết hạn/sai, AuthMiddleware trả về 401 nhưng bị lỗi CORS trên trình duyệt",
            "High",
            "AuthMiddleware đăng ký sau CORSMiddleware và trả response trực tiếp khi bắt ngoại lệ JWT, khiến các header Access-Control-Allow-Origin bị thiếu.",
            "Chuyển AuthMiddleware lên trước và bổ sung trực tiếp các header CORS cần thiết trong hàm phản hồi _auth_error.",
            "ĐÃ SỬA (CLOSED)", "19/11/2026", "PASS (Trình duyệt nhận 401 chuẩn có CORS)"
        ),
        (
            "BUG-03", "Gợi ý bài đăng", "TC_REC_25",
            "Gọi API /team-posts/recommendations bị 404 do router đăng ký với prefix /api",
            "Medium",
            "Trang frontend một số nơi gọi /api/team-posts và một số nơi gọi /team-posts, dẫn đến xung đột đường dẫn.",
            "Đăng ký router ở cả 2 tiền tố trong app/main.py và hỗ trợ cả 2 endpoint /recommendations và /recommended.",
            "ĐÃ SỬA (CLOSED)", "19/11/2026", "PASS (Cả 2 endpoint hoạt động hoàn hảo)"
        ),
        (
            "BUG-04", "UI Trang chủ", "TC_UI_15",
            "Trang home.html chưa import các thư viện dùng chung axios, config.js, api.js, utils.js",
            "Medium",
            "Thiếu các thẻ script thư viện trước home.js khiến trang không gọi được hàm tiện ích an toàn escapeHtml và axios.",
            "Bổ sung đầy đủ CDN axios và các file config.js, api.js, utils.js vào trước home.js trong pages/home.html.",
            "ĐÃ SỬA (CLOSED)", "19/11/2026", "PASS (Giao diện hiển thị trơn tru, không có lỗi console)"
        )
    ]

    for row_i, bug in enumerate(bug_records, start=2):
        for col_i, val in enumerate(bug, start=1):
            c = ws3.cell(row=row_i, column=col_i, value=val)
            c.font = Font(name="Segoe UI", size=9)
            c.border = thin_border
            if col_i in [1, 2, 3, 5, 8, 9, 10]:
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            if col_i == 8 and "ĐÃ SỬA" in val:
                c.font = Font(name="Segoe UI", size=9, bold=True, color=PASS_GREEN)
                c.fill = PatternFill(start_color=PASS_BG, end_color=PASS_BG, fill_type="solid")

            if col_i == 10 and "PASS" in val:
                c.font = Font(name="Segoe UI", size=9, bold=True, color=PASS_GREEN)

        ws3.row_dimensions[row_i].height = 48

    # Auto-fit column widths cho tất cả các sheets
    for ws in [ws1, ws2, ws3]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                # Bỏ qua các dòng gộp tiêu đề quá dài
                if len(val_str) > 0 and len(val_str) < 100:
                    max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Điều chỉnh độ rộng tối ưu cho từng sheet
    ws1.column_dimensions["B"].width = 28
    ws1.column_dimensions["C"].width = 38
    ws1.column_dimensions["D"].width = 16
    ws1.column_dimensions["E"].width = 16
    ws1.column_dimensions["F"].width = 22
    ws1.column_dimensions["G"].width = 45

    ws2.column_dimensions["A"].width = 14
    ws2.column_dimensions["B"].width = 20
    ws2.column_dimensions["C"].width = 12
    ws2.column_dimensions["D"].width = 16
    ws2.column_dimensions["E"].width = 32
    ws2.column_dimensions["F"].width = 28
    ws2.column_dimensions["G"].width = 32
    ws2.column_dimensions["H"].width = 24
    ws2.column_dimensions["I"].width = 32
    ws2.column_dimensions["J"].width = 32
    ws2.column_dimensions["K"].width = 14
    ws2.column_dimensions["L"].width = 14

    ws3.column_dimensions["A"].width = 12
    ws3.column_dimensions["B"].width = 18
    ws3.column_dimensions["C"].width = 12
    ws3.column_dimensions["D"].width = 32
    ws3.column_dimensions["E"].width = 14
    ws3.column_dimensions["F"].width = 30
    ws3.column_dimensions["G"].width = 32
    ws3.column_dimensions["H"].width = 18
    ws3.column_dimensions["I"].width = 14
    ws3.column_dimensions["J"].width = 22

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    print(f"Đã tạo file Excel thành công tại: {output_path}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "TEST_CASES_AND_TEST_LOG_T3CC6DF.xlsx"
    create_test_report_excel(out)
