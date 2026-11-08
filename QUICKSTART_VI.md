# MECHAVISION AI — BẮT ĐẦU Ở ĐÂY

## Bạn nhận được gì?

Dự án Python đầy đủ mã nguồn: mô hình động học, bộ lọc EKF có ràng buộc vật lý, bộ mô phỏng, ba phương pháp đối chứng, camera/video, đo bằng marker màu/ArUco hoặc model YOLO Pose tự huấn luyện, dashboard desktop, lưu phiên CSV, công cụ tạo nhãn/huấn luyện và thí nghiệm đánh giá. Xem `README.md` và `docs/RESEARCH_PROTOCOL.md` để hiểu giới hạn nghiên cứu.

**Bản phát hành chưa chứa trọng số AI cho động cơ thật và chưa có dữ liệu đo thực tế.** Bạn cần quay video, gán nhãn, đo thông số hình học và huấn luyện; không được tuyên bố hệ thống đã nhận diện chính xác LEGO thật trước khi thử.

## Mở ứng dụng mô phỏng ngay trên Windows

1. Giải nén ZIP vào thư mục không dấu, ví dụ `D:\Projects\MechaVision-AI`.
2. Cài Python 3.12, mở PowerShell ở thư mục vừa giải nén.
3. Chạy:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
.venv\Scripts\python.exe -m mechavision gui
```

4. Trong màn hình, `Source = simulation` → `Start analysis`. Dòng **SIMULATED DATA** nghĩa là dữ liệu ảo, không phải camera thật.

## Chạy thử thuật toán và kiểm thử

```powershell
.venv\Scripts\python.exe -m mechavision evaluate --seconds 24 --fps 30 --out outputs/evaluation
.venv\Scripts\python.exe -m pytest -q
```

Kết quả trong `outputs/evaluation/summary.json` và `ablation.csv`. Con số chỉ đo trên mô phỏng.

## Bắt đầu với động cơ thật

1. Tháo cụm động cơ, xác minh loại cơ cấu và các khớp nhìn thấy được.
2. Gắn camera cố định, thu 3+ video ngắn ở các tốc độ/ánh sáng khác nhau.
3. Dùng `mechavision calibrate --source 0 --out outputs/calibration.json` để nhấn bốn điểm hình học.
4. Nếu gắn được marker **chính xác lên tâm các khớp**, có thể dùng ArUco hoặc sticker đỏ/xanh lá/xanh dương để thử nghiệm trước khi huấn luyện AI.
5. Dùng `mechavision extract`, `annotate`, `split`, `train`, `validate` theo README để huấn luyện YOLO Pose trên động cơ thật. Có thể dùng đường nhanh `annotate --video` và `init-dataset`.
6. Chạy camera live với dữ liệu thực và checkpoint của bạn; thu bảng ground truth độc lập để đánh giá.

## Đưa lên GitHub

Hiện không kèm liên kết kho đã xuất bản. Tạo **repository trống** `MechaVision-AI` trên tài khoản GitHub của bạn rồi dùng lệnh `git init`, `git add`, `git commit`, `git remote add origin`, `git push` ở cuối `README.md` để xuất bản. Sau khi đó mới dùng `git clone` để tải từ GitHub.
