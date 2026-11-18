USE app_db;

-- Chạy truy vấn này trước để kiểm tra dữ liệu báo cáo bị trùng.
SELECT reporter_id, target_type, target_id, COUNT(*) AS total
FROM reports
GROUP BY reporter_id, target_type, target_id
HAVING COUNT(*) > 1;

-- Sau khi xử lý các dòng trùng (nếu có), chạy lệnh dưới đây một lần.
ALTER TABLE reports
ADD CONSTRAINT uq_reports_reporter_target
UNIQUE (reporter_id, target_type, target_id);
