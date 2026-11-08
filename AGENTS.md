# Hướng dẫn tiếp tục MechaVision AI

Đọc [docs/HANDOFF.md](docs/HANDOFF.md), [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) và [docs/ROADMAP.md](docs/ROADMAP.md) trước khi thay đổi. Đây là nguyên mẫu nghiên cứu thị giác máy tính cho cơ cấu tay quay–con trượt; chưa có kết quả vật lý trên LEGO được xác minh.

- Nhánh bàn giao: `feature/premium-dashboard-v3`, từ V2.1 `65a448a`. Không tự merge `main`. Đọc `git status -sb` và `git log -3 --oneline` để biết trạng thái thật; không suy đoán đã push từ tên nhánh.
- Giữ nguyên thuật toán YOLO Pose, EKF, động học và quy trình đánh giá khi sửa UI. Không đổi khóa `Observation`, `Estimate`, CSV, API/CLI, thứ tự `pivot` / `crank` / `piston`, đơn vị nội bộ hoặc giao diện `Worker.sample` để trang trí dashboard.
- Mọi KPI, confidence và xu hướng phải lấy từ quan sát/kết quả hiện có. Thiếu dữ liệu hiển thị `—`; biểu đồ giữ khoảng trống. Mô phỏng, video và camera phải phân biệt rõ. Confidence detector không được gọi là xác suất đúng hoặc độ chính xác trên LEGO.
- Twin chỉ dựng từ `TRACKING` hoặc `PREDICTED`; dự báo có nhãn. Không tự tạo chuyển động khi mất dấu. Cận cảnh/zoom chỉ đổi phép vẽ, không đổi tọa độ đo.
- Camera, detector, EKF, CSV và đánh giá chạy trên worker nền. UI chỉ đọc trạng thái và vẽ. Không thêm thư viện nặng khi chưa có nhu cầu cụ thể.
- Giữ nội dung người dùng bằng tiếng Việt; giữ nguyên tên hàm/biến/module, API và cú pháp cài đặt.
- Kiểm tra bằng `python -m pytest -q`, `python -m compileall -q src tools/verify_dashboard.py`. Khi sửa UI, dùng `tools/verify_dashboard.py`, xem ảnh 1366×768/1920×1080 và đọc kích thước thực tế trong JSON. Không tuyên bố đạt thẩm mỹ thương mại chỉ từ việc test xanh.
- Không ghi CSV/video sinh bởi QA thành dữ liệu đo thật, không commit `.venv`, cache hoặc thông tin xác thực. `outputs/` bị bỏ qua; ảnh QA có chủ đích nằm trong `assets/`.

V3 được chốt sớm theo yêu cầu tiết kiệm hạn mức; hạng mục thiết kế còn thiếu được ghi trong HANDOFF. Tiếp tục theo yêu cầu mới của người dùng, không tự mở rộng tính năng hoặc huấn luyện không có dữ liệu.
