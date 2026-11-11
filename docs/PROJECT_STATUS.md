# Cập nhật Phase 2 — 11/11/2026

Nhánh hiện tại: `feature/phase2-real-vision`, tạo từ V4 `fe235e5` sau khi xác minh working tree sạch. Không reset, redesign, push hoặc merge main. Các ghi chú V4 phía dưới là lịch sử bản nền, không phải HEAD hiện tại.

Đã bổ sung tạm dừng/tiếp tục bằng nút phiên hiện có, pacing video theo timestamp, phân biệt mất camera với EOF video và giải phóng handle lỗi. Không thay Geometry/EKF/YOLO adapter/schema dữ liệu. CPU fallback dùng detector marker hoặc thiết bị YOLO `cpu` được chọn rõ ràng.

Kiểm chứng: 60 test liên quan đạt (5 test mới), 2 test video/vòng đời chạy lại trên Windows native đạt; compileall đạt. Fixture video tổng hợp xác minh decoder → detector → EKF → Twin → CSV, che pít-tông, mất dấu/phục hồi và pause/resume/stop. Chưa đo camera/LEGO thật, YOLO riêng hoặc latency toàn trình. Không đóng gói release Phase 2.

Đọc [PHASE2_VALIDATION.md](PHASE2_VALIDATION.md) để chạy demo, tái lập kiểm thử, chuẩn bị tham chiếu độc lập và biết giới hạn camera/driver. Bước kế tiếp: camera thật → hiệu chuẩn LEGO → dữ liệu độc lập → đánh giá EKF; không dùng fixture làm kết quả vật lý.

---

# Trạng thái dự án — bàn giao V4

Cập nhật 11/11/2026. Nhánh `feature/ultimate-dashboard-v4`, nền V3 `902d804833996aacf3b5ea5054314cd0150cbece`.
Commit cuối là HEAD của bản bàn giao; mã đầy đủ nằm trong manifest.json đi kèm ZIP/bundle và được xác định bằng `git log -1 --format=fuller`. Không tự ghi hash của chính commit vào nội dung commit đó.
V4 được commit cục bộ; không push, không tạo PR, không merge main trong lượt phát hành.

## Đã triển khai và xác minh

- Bốn trang Giám sát, Phân tích, Thực nghiệm và Cài đặt dùng design system V4. Giám sát giữ Camera/Twin 56:44, KPI/xu hướng/trạng thái ở dải dưới.
- Camera cận cảnh/toàn khung, zoom/pan/fit, bật/tắt annotation từ ảnh thô; Twin cơ khí đồng tỷ lệ, chỉ hiển thị trạng thái theo dõi hoặc dự báo hợp lệ.
- Phân tích có góc ba phương pháp, tọa độ pít-tông, RPM, residual, uncertainty, confidence, FPS và thời gian Processor.step. Thời gian này không phải độ trễ toàn trình.
- Thực nghiệm dùng đánh giá nền thật của pipeline, bảng kết quả, lịch sử phiên và đường dẫn rút gọn có sao chép đầy đủ. Export CSV đối chiếu đúng byte với kết quả đánh giá; JSON do pipeline hiện có tạo.
- Cài đặt phân nhóm nguồn/nhận diện, hình học/EKF, hiển thị/lưu trữ; khóa cấu hình khi đang thu nhận và áp dụng nguồn ở phiên tiếp theo. Tham số EKF chỉ đọc, không có điều khiển giả.
- Bắt đầu/dừng mô phỏng, đổi trang, nguồn video qua decoder/dấu màu/EKF, dự báo/mất dấu, kết nối camera/báo lỗi đã chạy trên Windows.
- **85 kiểm thử đạt, 0 thất bại**, toàn bộ suite chạy một lần; compileall src/tools đạt. [Nhật ký](../assets/dashboard-v4/pytest.txt).
- 84 ảnh QA: 42 offscreen đúng kích thước và 42 Windows native; bao phủ bốn trang cùng các tab ở 1366×768, 1600×900, 1920×1080 yêu cầu. Không có bounds issue do công cụ phát hiện. Đã xem ảnh trực quan; không phát hiện lỗi nghiêm trọng cần sửa trong lượt chốt.
- Góc tích lũy **671,5183°** giữ đúng trên KPI và đường EKF vật lý: thiết kế là góc liên tục, không modulo 360. [Bằng chứng](../assets/dashboard-v4/angle-check.txt).
- Các module thuật toán lõi không đổi; controller chỉ bổ sung truyền ảnh thô để UI điều khiển lớp phủ.

## Giới hạn

Camera 0 không mở được: chỉ xác minh lỗi kết nối, chưa có luồng camera vật lý. Chưa xác minh LEGO thật, hiệu chuẩn vật lý, YOLO Pose trọng số LEGO riêng, tham chiếu góc độc lập hoặc độ chính xác EKF thực nghiệm. Mô phỏng/video fixture chỉ kiểm tra phần mềm.
Windows native bị giới hạn một số cửa sổ yêu cầu 1920×1080 thành 1920×1055; JSON ghi kích thước thực. Offscreen kiểm đủ kích thước chính xác. Lượt native dùng scale-factor 0.8 trên desktop DPI 125%, DPR ghi nhận 1; chưa bao phủ toàn bộ tổ hợp DPI/màn hình. Chưa benchmark RTX 3050 Ti hay độ trễ toàn trình.
Không tuyên bố đạt chất lượng thương mại Sentinex chỉ dựa trên test hoặc screenshot.

Xem [báo cáo](../BAO_CAO_V4.md), [khôi phục và tiếp tục](HANDOFF.md), [QA Windows](../assets/dashboard-v4/windows/qa-result.json), [QA đúng kích thước](../assets/dashboard-v4/exact/qa-result.json).

Kiểm tra lint bổ sung: Ruff còn 116 cảnh báo/lỗi quy tắc trên src/tools/tests (gồm định dạng/import và chất lượng mã); chưa xử lý hàng loạt trong lượt phát hành để tránh thay đổi ngoài phạm vi. Đây không phải lỗi pytest. Nhật ký: assets/dashboard-v4/ruff.txt.
