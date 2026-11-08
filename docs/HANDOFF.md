# Bàn giao cho phiên Codex tiếp theo

## Đọc trước và xác định mốc

Đọc [AGENTS.md](../AGENTS.md), [PROJECT_STATUS.md](PROJECT_STATUS.md), [ARCHITECTURE.md](ARCHITECTURE.md) và [ROADMAP.md](ROADMAP.md). Người dùng yêu cầu chốt sớm V3 do hạn mức còn 12%, không tiếp tục chỉnh thẩm mỹ nhỏ hoặc mở rộng tính năng. Chưa nghiệm thu mức tương đương thiết kế tham chiếu thương mại. Không sao chép tên/logo/chức năng kiểm tra lỗi sản phẩm của ảnh tham chiếu.

Nhánh `feature/premium-dashboard-v3`; nền `65a448a`, mốc mã V3 `c7228c5`. Commit tài liệu cuối chính là `HEAD` của bundle; hash cuối nằm trong manifest/báo cáo bên cạnh bundle. Chưa push/PR V3, không merge main. Đừng coi trạng thái remote-tracking cũ là đã đồng bộ GitHub.

```powershell
git status -sb
git log -3 --oneline
git remote -v
```

## Khôi phục khi chưa push

ZIP chứa mã nguồn/tài liệu/kiểm thử/ảnh đã theo dõi, không có `.git` hoặc môi trường `.venv`. Bundle chứa nhánh V3 và lịch sử Git đầy đủ. Thay đường dẫn ví dụ bằng nơi đã lưu tệp bàn giao:

```powershell
git clone -b feature/premium-dashboard-v3 "C:\duong-dan\MechaVision-AI-Dashboard-V3.bundle" MechaVision-AI
cd MechaVision-AI
git log -1 --format=fuller
git status -sb
```

Nếu đã có clone khác, nhập bundle vào nhánh review mới, không ghi đè thay đổi đang làm:

```powershell
git fetch "C:\duong-dan\MechaVision-AI-Dashboard-V3.bundle" feature/premium-dashboard-v3
git switch -c review/dashboard-v3 FETCH_HEAD
```

Clone từ bundle có thể đặt `origin` trỏ tới tệp bundle. Kiểm tra `git remote -v` trước khi cập nhật remote; repository đích là `https://github.com/KienTruowng/MechaVision-AI.git`. Tài liệu này chỉ hướng dẫn khôi phục; không có thao tác tự merge/push.

## Môi trường và chạy ứng dụng

Python 3.11–3.13, khuyến nghị 3.12. Đã QA bằng Python 3.12.13, PySide6 6.12.0, PyQtGraph 0.14.0 trên Windows. Không đóng gói interpreter hoặc phụ thuộc vào ZIP. Cần phông Unicode hệ thống (Segoe UI trên Windows).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
.venv\Scripts\python.exe -m mechavision gui
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m compileall -q src tools/verify_dashboard.py
```

YOLO tùy chọn dùng nhóm `train`; chưa có trọng số LEGO riêng để thử. Chạy mô phỏng trước: Cài đặt → Mô phỏng → Bắt đầu phiên. Camera/video yêu cầu JSON hiệu chuẩn; file cấu hình mẫu không xác nhận hiệu chuẩn vật lý.

```powershell
.venv\Scripts\python.exe tools/verify_dashboard.py --out outputs/dashboard-v3-qa/exact --camera
.venv\Scripts\python.exe tools/verify_dashboard.py --native --scale-factor 0.8 --out outputs/dashboard-v3-qa/windows --camera
```

`0.8` dùng cho tiến trình QA trên máy Windows đặt DPI 125%, không đổi cấu hình màn hình hệ thống. Đọc kích thước thực trong JSON. Công cụ tạo video dấu màu tổng hợp để thử decoder/EKF/mất dấu, không phải video LEGO thật. Nếu sandbox không ghi được thư mục tạm, đặt `TEMP` và `TMP` vào một thư mục có quyền ghi trong workspace rồi chạy lại pytest; không bỏ qua lỗi kiểm thử.

## Bản đồ nhanh và hợp đồng kỹ thuật

- `src/mechavision/gui.py`: vòng đời phiên, signal/slot, điểm vào `launch()` và các alias giao diện giữ tương thích.
- `dashboard_shell/widgets/theme/monitoring/analytics/settings/experiments.py`: shell/component/theme và bốn trang; `render.py` là phép vẽ BGR, `i18n.py` vẽ Unicode.
- `dashboard_controller.py`: Worker/QThread giữ pipeline; `dashboard_state.py`: bộ đệm 3.600 mẫu và số khung tổng. Sparkline chỉ lấy 90 mẫu cuối, FPS dùng chuỗi hiện có.
- `geometry.py`, `estimators.py`, `processing.py`: động học, EKF và xử lý. `detection.py`, `acquisition.py`, `synthetic.py`: detector, nguồn thu nhận và mô phỏng. `session.py`, các module evaluation, dataset/train: ghi phiên, đánh giá và dữ liệu/huấn luyện.
- `tests/`, `tools/verify_dashboard.py`, `assets/dashboard-v3/`: bằng chứng kiểm thử; `configs/`: hình học mẫu; `docs/`: tài liệu. `outputs/`, `.venv` và cache được bỏ qua.

Không đổi các API/khóa dữ liệu để phục vụ UI. Đơn vị nội bộ: pixel, giây, radian, rad/s; UI đổi sang độ/vòng phút. Ba điểm `pivot`, `crank`, `piston`; trạng thái `TRACKING`, `PREDICTED`, `LOST`, `UNINITIALIZED`. Giá trị thiếu không được đổi thành 0. CSV giữ tên cột và `truth_rad_synthetic_only` chỉ là truth mô phỏng. Twin là kết quả ước lượng, không phải cảm biến độc lập; confidence detector không phải độ chính xác mô hình.

## Kiểm chứng cuối và việc còn lại

60 test đạt, compileall đạt, AST thuật toán không đổi. Hai lượt QA ×18 ảnh; khởi động, bắt đầu/dừng/đổi trang, cận cảnh/zoom, đánh giá nền, video và trạng thái dự báo/mất dấu/lỗi camera đã chạy. Xem nhật ký và giới hạn trong PROJECT_STATUS. Camera 0 không mở được; chưa có kiểm chứng vật lý LEGO, YOLO riêng hoặc đánh giá EKF trên dữ liệu thực. Ưu tiên tiếp theo là camera/hiệu chuẩn, thu dữ liệu LEGO, nhãn/huấn luyện YOLO Pose và tham chiếu độc lập trước khi công bố kết quả thực nghiệm.
