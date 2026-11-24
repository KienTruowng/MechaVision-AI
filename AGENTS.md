# Hướng dẫn tiếp tục MechaVision AI

Đọc [docs/HANDOFF.md](docs/HANDOFF.md), [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) và [docs/ROADMAP.md](docs/ROADMAP.md) trước khi thay đổi. Đây là nguyên mẫu nghiên cứu thị giác máy tính cho cơ cấu tay quay–con trượt; chưa có kết quả vật lý trên LEGO được xác minh.

- Nhánh V4: `feature/ultimate-dashboard-v4`, tạo từ V3 `902d804833996aacf3b5ea5054314cd0150cbece`. Không tự merge `main`, force push hoặc xóa lịch sử. Đọc `git status -sb` và `git log -3 --oneline` để biết trạng thái thật; không suy đoán đã push từ tên nhánh.
- Giữ nguyên thuật toán YOLO Pose, EKF, động học và quy trình đánh giá khi sửa UI. Không đổi khóa `Observation`, `Estimate`, CSV, API/CLI, thứ tự `pivot` / `crank` / `piston`, đơn vị nội bộ hoặc giao diện `Worker.sample` để trang trí dashboard.
- Mọi KPI, confidence và xu hướng phải lấy từ quan sát/kết quả hiện có. Thiếu dữ liệu hiển thị `—`; biểu đồ giữ khoảng trống. Mô phỏng, video và camera phải phân biệt rõ. Confidence detector không được gọi là xác suất đúng hoặc độ chính xác trên LEGO.
- Twin chỉ dựng từ `TRACKING` hoặc `PREDICTED`; dự báo có nhãn. Không tự tạo chuyển động khi mất dấu. Cận cảnh/zoom chỉ đổi phép vẽ, không đổi tọa độ đo.
- Camera, detector, EKF, CSV và đánh giá chạy trên worker nền. UI chỉ đọc trạng thái và vẽ. Không thêm thư viện nặng khi chưa có nhu cầu cụ thể.
- Giữ nội dung người dùng bằng tiếng Việt; giữ nguyên tên hàm/biến/module, API và cú pháp cài đặt.
- Kiểm tra bằng `python -m pytest -q`, `python -m compileall -q src tools`. Khi sửa UI, dùng `tools/verify_dashboard.py`, xem ảnh 1366×768/1600×900/1920×1080 và đọc kích thước thực tế trong JSON. Dùng `tools/compare_dashboard.py` để ghép ảnh thực tế V3/V4; không tuyên bố đạt thẩm mỹ thương mại chỉ từ việc test xanh.
- Không ghi CSV/video sinh bởi QA thành dữ liệu đo thật, không commit `.venv`, cache hoặc thông tin xác thực. `outputs/` bị bỏ qua; ảnh QA có chủ đích nằm trong `assets/`.

V3 là mốc nền, không phải nhánh để tiếp tục sửa V4. Yêu cầu V4 cho phép quyết định thiết kế thông thường trong phạm vi repository; kiểm thử và đối chiếu ảnh trước khi bàn giao. Điều khiển chưa được pipeline hỗ trợ phải ghi rõ chưa khả dụng. Không suy ra latency từ nghịch đảo FPS; không lấy confidence của detector làm độ chính xác thực nghiệm. Trạng thái cuối và giới hạn được ghi trong [BAO_CAO_V4.md](BAO_CAO_V4.md).

Phase 2 hiện tại: `feature/phase2-real-vision`, nền V4 `fe235e5`. Giữ baseline UI; đọc docs/PHASE2_VALIDATION.md và phần đầu HANDOFF.md. Không hiểu các ghi chú V4 lịch sử là HEAD hiện tại.
