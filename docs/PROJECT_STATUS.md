# Phase 2.1 — readiness, 11/11/2026

Nhánh `feature/phase2-real-vision`, tiếp tục từ `f305060`. Không redesign V4, không đổi YOLO Pose/EKF/kinematics/renderer hoặc cột CSV. Bản V4 gốc vẫn là `fe235e5`.

- Thu nhận từ chối ảnh rỗng/sai định dạng, giải phóng handle khi lỗi; timestamp video lặp sau giá trị hợp lệ không còn tiến chỉ 1 microsecond mỗi khung.
- Watchdog UI: quá 15 giây không tiến triển sẽ báo lỗi và yêu cầu stop; chặn mẫu đến muộn. Pause và pacing cập nhật heartbeat nên không gây timeout giả. Đóng cửa sổ khi đang thu nhận không wait trên UI thread; chờ signal finished trước đóng. Không terminate worker/driver. Timeout cũng có thể xảy ra khi tải mô hình/suy luận rất chậm; cần kiểm chứng máy đích.
- Hiệu chuẩn dùng cùng FrameSource với dashboard (camera yêu cầu 960×540, kích thước thực do driver quyết định). Lưu geometry JSON tương thích và `.calibration.json` chứa kích thước ảnh, hash geometry, đơn vị và tỷ lệ mm tùy chọn. Worker từ chối ảnh khác kích thước hoặc geometry thay đổi sau hiệu chuẩn; cấu hình cũ thiếu sidecar vẫn đọc được nhưng không xác minh độ phân giải.
- Mỗi phiên dashboard có `.metadata.json` cạnh CSV: nguồn, detector/device, geometry snapshot, độ phân giải nguồn, thời gian UTC và thời gian quan sát, số khung/trạng thái tracking, kết thúc/lỗi. `simulation` hoặc `unverified_capture`; camera/video không tự được chứng nhận vật lý. Không có ground truth thì accuracy chưa khả dụng, latency là null. Sidecar không sửa schema đánh giá hiện có.
- Cleanup luôn phát tín hiệu kết thúc kể cả lỗi lưu/đóng. Metadata cập nhật lúc khởi tạo, biết kích thước nguồn và kết thúc; nếu tiến trình bị kill, trạng thái running không phải kết thúc thành công. Không ghi metadata mỗi frame để tránh I/O không cần thiết.

Kiểm chứng: 50 test liên quan đạt; 3 test Windows native đạt (2 test chạy lại + 1 test mới, tổng 51 test khác nhau). Compileall src/tools đạt. Native bao gồm video fixture có đổi tốc độ/che khuất/phục hồi, pause/resume/stop và capture giả lập bị chặn: UI còn phản hồi, close không chờ đồng bộ, hủy hợp tác rồi đóng tài nguyên. Lần chạy đầu có 1 test timestamp thất bại do sai lệch 1 microsecond; đã sửa logic và nhóm 50 test chạy lại đạt. Không chạy toàn bộ QA dashboard.

Chưa xác minh LEGO/camera vật lý/YOLO riêng/GPU/latency toàn trình. Chưa có dữ liệu ground truth để công bố MAE/RMSE/P95 vật lý. Driver bị chặn vẫn có thể giữ worker đến khi read/open trả về; không thể bảo đảm cưỡng chế đóng mọi backend Windows. Không claim kiểm thử rò rỉ bộ nhớ dài hạn. Confidence marker là trọng số quy ước/điểm hình dạng, không phải độ chính xác đã hiệu chuẩn.

Đọc [PHASE2_VALIDATION.md](PHASE2_VALIDATION.md) để chạy và chuẩn bị dữ liệu.

---

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
