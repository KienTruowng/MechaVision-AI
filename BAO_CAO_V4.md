# Báo cáo bàn giao Dashboard V4

Ngày 11/11/2026. Nhánh `feature/ultimate-dashboard-v4`, nền V3 `902d804`. Commit cuối xác định bằng HEAD và manifest.json ngoài gói. Không push, không PR, không merge main.

## Phạm vi hoàn thành

Bốn trang V4 đã hoàn thiện: Camera/Twin 56:44, dải KPI/xu hướng/phiên phía dưới; camera zoom/pan/fit và lớp phủ có thể tắt; Twin cơ khí có bearing/crank/rod/piston/rails từ trạng thái ước lượng. Analytics gồm động học, chất lượng quan sát và hiệu năng; Experiment Lab dùng CSV/JSON thực của pipeline; Settings có nhóm cấu hình và giải thích trạng thái khóa. Không thêm thư viện nặng hoặc thay thuật toán nghiên cứu.

## Nghiệm thu cuối

- Toàn bộ suite: **85 đạt, 0 thất bại**, chạy một lần; compileall src/tools đạt.
- 42 ảnh offscreen + 42 Windows native, bốn trang/các tab ở ba kích thước yêu cầu; không phát hiện bounds issue. Đã xem ảnh và không phát hiện lỗi nghiêm trọng cần sửa trong lượt phát hành.
- Đã kiểm tra bắt đầu/dừng, đổi trang, cấu hình nguồn cho phiên kế tiếp, cận cảnh/toàn khung, zoom/pan/fit, annotation, video fixture qua decoder/detector/EKF, dự báo/mất dấu, báo lỗi camera và xuất CSV khớp kết quả đánh giá.
- Góc tích lũy 671,5183° đúng giữa KPI/biểu đồ; thiết kế không giới hạn 0–360°.
- Không sửa mã chức năng trong lượt FINAL QA: không có lỗi tái hiện mới. Các sửa UI và regression của các lượt V4 trước được bảo toàn trong commit bàn giao.
- Thuật toán Geometry/EKF/detection/evaluation và cấu trúc dữ liệu lõi không đổi so với nền V3. Controller bổ sung ảnh thô để điều khiển annotation.

## Bằng chứng và gói khôi phục

Ảnh/log/JSON tại `assets/dashboard-v4/`; ảnh V3 giữ tại `assets/dashboard-v3/`. Bộ bàn giao ngoài repository gồm MechaVision-AI-Dashboard-V4.zip, MechaVision-AI-Dashboard-V4.bundle và manifest.json (commit đầy đủ, SHA-256, kết quả đối chiếu ZIP và clone bundle). ZIP chứa mã nguồn và ảnh đã commit, không gồm môi trường ảo/cache/dữ liệu chạy. Bundle giữ đầy đủ lịch sử nhánh V4.
Hướng dẫn chạy Windows và clone bundle: [docs/HANDOFF.md](docs/HANDOFF.md).

## Giới hạn chưa kiểm chứng

Camera 0 không mở được; đã xác minh báo lỗi, chưa xác minh camera vật lý/LEGO/hiệu chuẩn/YOLO riêng/độ chính xác EKF thực nghiệm. Synthetic chỉ là kiểm tra phần mềm. Thời gian xử lý không phải latency toàn trình. Chưa benchmark GPU.
Offscreen đúng 1366×768, 1600×900, 1920×1080. Windows native có một số cửa sổ bị giới hạn 1920×1055; JSON ghi kích thước thật. Native chạy scale-factor 0.8 trên desktop 125%, DPR 1; chưa bao phủ mọi mức DPI. Không tuyên bố tương đương Sentinex hoặc phần mềm thương mại.

Kiểm tra lint bổ sung: Ruff còn 116 cảnh báo/lỗi quy tắc trên src/tools/tests (gồm định dạng/import và chất lượng mã); chưa xử lý hàng loạt trong lượt phát hành để tránh thay đổi ngoài phạm vi. Đây không phải lỗi pytest. Nhật ký: assets/dashboard-v4/ruff.txt.
