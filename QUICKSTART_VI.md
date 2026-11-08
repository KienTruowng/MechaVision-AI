# MechaVision AI — Hướng dẫn bắt đầu

Dự án có mô hình động học, EKF có ràng buộc vật lý, bộ mô phỏng, ba phương pháp đối chứng, camera/video, dấu màu/ArUco, tích hợp YOLO Pose, bảng điều khiển máy tính, nhật ký CSV và công cụ dữ liệu/đánh giá. Xem [README](README.md) và [quy trình nghiên cứu](docs/RESEARCH_PROTOCOL.md) để hiểu giới hạn.

**Chưa kèm trọng số được huấn luyện trên động cơ thực và chưa có kết quả đo cơ cấu thực được kiểm chứng.** Cần quay video, gán nhãn, đo hình học và huấn luyện trước khi đưa ra tuyên bố về nhận diện AI.

## Mở mô phỏng trên Windows

Tải hoặc giải nén mã nguồn, cài Python 3.12 rồi mở PowerShell trong thư mục dự án:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
.venv\Scripts\python.exe -m mechavision gui
```

Chọn **Nguồn → Mô phỏng → Bắt đầu phân tích**. Nhãn **DỮ LIỆU MÔ PHỎNG** xác định dữ liệu tổng hợp. **Đang theo dõi**, **Đang dự báo**, **Mất dấu** và **Chưa khởi tạo** mô tả bộ ước lượng, không xác nhận nguồn dữ liệu là đo thực. Khi không đủ độ tin cậy, góc/tốc độ được để trống.

## Kiểm thử và chạy thuật toán

```powershell
.venv\Scripts\python.exe -m mechavision evaluate --seconds 24 --fps 30 --out outputs/evaluation
.venv\Scripts\python.exe -m pytest -q
```

Kết quả ở `outputs/evaluation/summary.json` và `ablation.csv`, chỉ đo trên mô phỏng.

## Bắt đầu đo cơ cấu thực

1. Xác minh loại cơ cấu và tâm các khớp có thể quan sát.
2. Gá camera cố định; thu ít nhất ba phiên độc lập với nhiều tốc độ/điều kiện sáng.
3. Chạy `mechavision calibrate --source 0 --out outputs/calibration.json`, chọn bốn điểm rồi nhấn Enter.
4. Nếu gắn dấu chuẩn chính xác lên tâm khớp, dùng ArUco hoặc dấu đỏ/xanh lá/xanh dương để tạo đối chứng trước khi huấn luyện AI.
5. Thực hiện `extract`, `annotate --folder`, `split`, `train`, `validate` theo README. Đường `annotate --video` có phím điều khiển khác và cần tự tổ chức các tập theo phiên.
6. Chọn **Camera trực tiếp** hoặc **Video đã ghi** trong giao diện, cung cấp đúng tệp hiệu chuẩn và trọng số nếu dùng YOLO Pose. Thu góc tham chiếu độc lập để đánh giá.

## Làm việc với GitHub

Repository hiện có: [KienTruowng/MechaVision-AI](https://github.com/KienTruowng/MechaVision-AI). Xem [hướng dẫn GitHub](PUSH_TO_GITHUB_VI.md) để tải mã và tạo nhánh/Pull Request. Không cần khởi tạo lại Git cho bản đã được clone.
