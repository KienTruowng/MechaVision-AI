# Dashboard V2.1 — Cải tiến khả năng quan sát và đọc thông tin

V2.1 phát triển trên V2 tại commit `7d899d9af1b2f04e886640d824a3a8442332878f`, trên nhánh `feature/premium-dashboard-v2`. Giữ nguyên bốn trang Giám sát, Phân tích, Thực nghiệm và Cài đặt.

## Thay đổi

- **Quan sát thị giác:** mặc định cận cảnh theo miền chuyển động toàn vòng của hình học hiệu chuẩn, có lề cho nhãn keypoint. Miền nhìn cố định trong phiên, không bám theo nhiễu từng khung. Nút **Cận cảnh / Toàn khung** chuyển cách xem; ảnh gốc, tọa độ detector và CSV giữ nguyên. Nếu cấu hình hiệu chuẩn không đúng khung nguồn, chuyển sang Toàn khung để kiểm tra lại.
- **Digital Twin:** vẽ theo kích thước viewport thực, dùng phép biến đổi đồng tỷ lệ và căn giữa miền chuyển động. Bổ sung ổ trục, khớp đồng tâm, tay quay, thanh truyền, pít-tông, ray dẫn hướng và ký hiệu O/C/S; hiển thị r/l/e theo cấu hình. Chỉ dựng cơ cấu từ `TRACKING` hoặc `PREDICTED`; dự báo được ghi rõ. Mất dấu không tiếp tục dựng chuyển động.
- **Typography và KPI:** chữ cơ bản 13 px, chữ phụ 12 px, tiêu đề panel 14 px, giá trị KPI 34 px và trạng thái 18 px. Góc/RPM dùng cyan; màu trạng thái giữ ý nghĩa theo dõi, cảnh báo và lỗi. Thu gọn khối xu hướng để dành thêm chiều cao cho hai viewport.
- Không bổ sung phụ thuộc, không sửa công thức động học, YOLO, EKF, khóa dữ liệu, thuật toán đánh giá hoặc luồng suy luận nền. `Worker.sample` và các API xử lý giữ nguyên.

## Ảnh trước và sau

Các ảnh mô phỏng lấy từ Simulator và Processor thật. Giá trị FPS phụ thuộc lần chạy; ảnh dùng kiểm tra bố cục, không dùng làm benchmark hoặc bằng chứng đo động cơ thực.

| Phiên bản | Giám sát 1366×768 | Giám sát 1920×1080 |
|---|---|---|
| V2 trước thay đổi | [Ảnh](../assets/dashboard-v2/monitoring-1366x768.png) | [Ảnh](../assets/dashboard-v2/monitoring-1920x1080.png) |
| V2.1 | [Ảnh](../assets/dashboard-v2.1/exact/monitoring-1366x768.png) | [Ảnh](../assets/dashboard-v2.1/exact/monitoring-1920x1080.png) |

| Trang V2.1 | 1366×768 | 1920×1080 |
|---|---|---|
| Phân tích | [Ảnh](../assets/dashboard-v2.1/exact/analytics-1366x768.png) | [Ảnh](../assets/dashboard-v2.1/exact/analytics-1920x1080.png) |
| Thực nghiệm | [Ảnh](../assets/dashboard-v2.1/exact/experiments-1366x768.png) | [Ảnh](../assets/dashboard-v2.1/exact/experiments-1920x1080.png) |
| Cài đặt | [Ảnh](../assets/dashboard-v2.1/exact/settings-1366x768.png) | [Ảnh](../assets/dashboard-v2.1/exact/settings-1920x1080.png) |

Đã lưu thêm ảnh chưa có dữ liệu, toàn khung, dự báo, mất dấu, đang kết nối và lỗi camera trong cùng thư mục. Ảnh cửa sổ Windows thật nằm trong `assets/dashboard-v2.1/windows`.

## Kiểm chứng

- Windows, Python 3.12.13, PySide6 6.12.0, PyQtGraph 0.14.0; Qt báo phông Segoe UI.
- `python -m pytest -q`: **58 kiểm thử đạt**. Năm trường hợp bổ sung xác minh cận cảnh không đổi ảnh/phép đo, miền nhìn bao phủ hình học quay/lệch tâm và Twin vẽ lại đúng cùng ước lượng khi đổi kích thước mà không tự chạy thời gian.
- `python -m compileall -q src tools/verify_dashboard.py`: đạt. Đối chiếu AST lõi nhận diện, mô phỏng, động học, bộ lọc và đánh giá với `origin/main`: không thay đổi tính toán.
- Chạy QWidget thật bằng QTest trên backend Qt offscreen và Windows native: bắt đầu/dừng, đổi trang khi chạy, cận cảnh/toàn khung, đánh giá nền, chọn nguồn video, decoder → detector dấu màu → EKF, dự báo/mất dấu, kết nối camera và phục hồi sau lỗi. Mỗi backend lưu 17 ảnh; không phát hiện QLabel bị cắt theo kiểm tra kích thước chữ. Đã xem trực quan ảnh các trang và Twin.
- Backend offscreen xác minh chính xác 1366×768 và 1920×1080. Windows native xác minh 1366×768; một số cửa sổ yêu cầu 1920×1080 bị hệ điều hành giới hạn vùng nội dung còn 1920×1055. Kích thước yêu cầu/thực tế và DPR được ghi riêng, không gọi ảnh 1055 px là ảnh 1080 px.
- Camera 0 không mở được; đã xác minh trạng thái kết nối và lỗi, chưa xác minh hình ảnh camera vật lý, hiệu chuẩn cơ cấu thật hoặc trọng số YOLO riêng. Video QA là fixture tổng hợp có nhãn rõ ràng; không phải thực nghiệm động cơ.

Biên bản máy đọc được: [kích thước chính xác](../assets/dashboard-v2.1/exact/qa-result.json), [Windows native](../assets/dashboard-v2.1/windows/qa-result.json).

Tái lập QA từ môi trường đã cài nhóm `gui` và `dev`:

```bash
python -m pytest -q
python tools/verify_dashboard.py --out outputs/dashboard-v2.1-qa/exact --camera
python tools/verify_dashboard.py --native --scale-factor 0.8 --out outputs/dashboard-v2.1-qa/windows --camera
```

`--scale-factor 0.8` dùng riêng cho tiến trình QA trên máy Windows đang đặt DPI 125%; không thay đổi thiết lập hiển thị của người dùng.
