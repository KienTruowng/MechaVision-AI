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

# Bàn giao MechaVision AI Dashboard V4

Ngày 11/11/2026. Đây là trạng thái phát hành V4, thay thế ghi chú làm dở V3/V4 trước đây.

## Git và nguyên tắc tiếp tục

- Nhánh: `feature/ultimate-dashboard-v4`; nền V3: `902d804833996aacf3b5ea5054314cd0150cbece`.
- Commit bàn giao: HEAD trong bundle; lấy hash chính xác từ manifest.json bên cạnh gói hoặc `git rev-parse HEAD` sau clone. Không tự tham chiếu hash trong commit chứa tài liệu.
- Đã chốt UI; không redesign nếu không có yêu cầu mới. Luôn kiểm tra `git status -sb` trước sửa; không reset/ghi đè thay đổi đang có.
- Không push, PR hoặc merge main trong đợt phát hành này. Kiểm tra remote thực tế trước mọi thao tác GitHub sau này.
- Repository hiện tại: `C:/Users/heyim/Documents/Codex/2026-11-09/h-y-l-m-vi-c/work/MechaVision-AI`.
- Gói bàn giao: `C:/Users/heyim/Documents/Codex/2026-11-09/h-y-l-m-vi-c/outputs/dashboard-v4-release/` gồm ZIP, bundle, manifest và báo cáo.

## Thiết lập Windows

Python 3.11–3.13, khuyến nghị môi trường ảo riêng. Từ thư mục repository:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
.venv\Scripts\python.exe -m mechavision gui
```

Nếu cần YOLO: cài thêm `.[train]`, cung cấp trọng số riêng và chọn thiết bị phù hợp. ZIP không kèm môi trường ảo hoặc trọng số LEGO chưa tồn tại. Bắt đầu với Cài đặt → Mô phỏng → Bắt đầu phiên. Dừng phiên trước đổi nguồn; hình học và detector áp dụng ở phiên tiếp theo, tùy chọn hiển thị áp dụng ngay.

## Cấu trúc và hợp đồng phải giữ

`src/mechavision/`: pipeline và UI; `tests/`: regression; `tools/`: QA; `configs/`: cấu hình mẫu; `docs/`: thiết kế/kiến trúc; `assets/dashboard-v4/`: bằng chứng QA; `outputs/`: dữ liệu chạy, không commit.
Đọc [ARCHITECTURE.md](ARCHITECTURE.md) trước sửa. Giữ `Observation`, `Estimate`, `Worker.sample(frame, twin, data)`, API/CLI và khóa CSV/JSON. Thứ tự điểm `pivot/crank/piston`, đơn vị pixel/giây/radian/rad/s không đổi. UI đổi sang độ/RPM. Không chỉnh YOLO Pose, EKF hoặc Geometry để làm hình đẹp hơn. `raw_frame` là signal bổ sung; không thay sample. Không lấp phép đo thiếu bằng số 0.
Góc hiển thị là góc tích lũy; >360° hợp lệ. Twin chỉ cập nhật TRACKING/PREDICTED, dự báo có nhãn; không tạo chuyển động khi mất dấu. Confidence không phải độ chính xác thực nghiệm. Thời gian Processor.step không bao gồm toàn bộ camera/detector/render.

## Kiểm chứng cuối

85 passed / 0 failed; syntax/import và toàn bộ suite đã chạy một lần. 84 ảnh QA của bốn trang và các tab, ba kích thước yêu cầu. Zoom/pan/fit, annotation, export CSV, mô phỏng, video fixture, stop/start, dự báo/mất dấu và lỗi camera đã kiểm tra. Góc 671,5183° nhất quán giữa KPI và biểu đồ.
Xem [PROJECT_STATUS.md](PROJECT_STATUS.md) và [báo cáo](../BAO_CAO_V4.md) để biết giới hạn DPI/kích thước native. Camera 0 không mở được; chưa kiểm chứng LEGO, YOLO riêng, độ chính xác vật lý hay benchmark GPU. Không dùng kết quả synthetic làm kết quả thực nghiệm.

Lệnh regression: `python -m pytest -q`. QA khi UI thay đổi: `python tools/verify_dashboard.py --out outputs/qa --camera`; thêm `--native --scale-factor 0.8` để tái lập đợt Windows vừa chạy. Đọc JSON kích thước thực, không chỉ tên ảnh.

## Khôi phục Git bundle

Tại thư mục chứa bundle, clone vào thư mục mới (không ghi đè repo đang làm):

```powershell
git clone -b feature/ultimate-dashboard-v4 MechaVision-AI-Dashboard-V4.bundle MechaVision-AI-restored
cd MechaVision-AI-restored
git bundle verify ../MechaVision-AI-Dashboard-V4.bundle
git log -1 --format=fuller
git status -sb
git remote -v
```

Bundle chứa lịch sử đầy đủ của nhánh V4. So sánh HEAD với manifest.json; origin sau clone là đường dẫn bundle, không phải GitHub. ZIP là mã nguồn của cùng commit, không có .git; dùng bundle để giữ lịch sử. Gói đã được kiểm CRC/blob và clone thử bởi script đóng gói, kết quả ghi trong manifest bên ngoài commit.

## Tiếp theo

1. Kiểm tra camera thật, quyền Windows, backend và khung hình trước khi lắp LEGO; xác minh mất dấu/phục hồi trên nguồn thật.
2. Hiệu chuẩn hình học, thu video LEGO nhiều phiên/tốc độ/ánh sáng; tách train/validation/test theo phiên.
3. Gán nhãn ba điểm, huấn luyện YOLO Pose; lưu nguồn gốc dữ liệu/trọng số và đánh giá tập độc lập.
4. Thu góc tham chiếu độc lập/encoder, so sánh thị giác trực tiếp/EKF thời gian/EKF vật lý; báo cáo MAE/RMSE/P95, độ bao phủ và bất định theo phiên.
5. Đo FPS/latency thực trên máy đích và kiểm tra DPI bổ sung. Chỉ sửa lỗi tái hiện, giữ baseline V4.

Kiểm tra lint bổ sung: Ruff còn 116 cảnh báo/lỗi quy tắc trên src/tools/tests (gồm định dạng/import và chất lượng mã); chưa xử lý hàng loạt trong lượt phát hành để tránh thay đổi ngoài phạm vi. Đây không phải lỗi pytest. Nhật ký: assets/dashboard-v4/ruff.txt.
