# Trạng thái dự án — bàn giao V3

Cập nhật 09/11/2026. Repository: `KienTruowng/MechaVision-AI`.

## Mốc Git

- Nhánh: `feature/premium-dashboard-v3`, tạo trực tiếp từ V2.1 `65a448afd96be2f1d699ae34115a0e71edd92117`.
- Commit mã giao diện V3 đã kiểm thử: `c7228c5330cbe589a6d4e095031dec988239da74`.
- Commit cuối của gói bàn giao là `HEAD`, gồm bổ sung tài liệu sau mốc mã trên. Xác định chính xác bằng `git log -1 --format=fuller`; mã đầy đủ được ghi trong `manifest.json` và báo cáo đi cùng ZIP/bundle, tránh tự tham chiếu hash của chính commit chứa tài liệu.
- Commit cục bộ, chưa push và chưa tạo PR cho V3. Kết nối GitHub trước đây trả 403; Git Credential Manager không dùng được trong sandbox. Không thử lại xác thực trong giai đoạn chốt V3. Không merge `main`.

## Đã triển khai và kiểm tra

- Bốn trang Giám sát, Phân tích, Thực nghiệm và Cài đặt; vòng đời bắt đầu/dừng/kết nối/lỗi và khóa cấu hình khi chạy.
- Sidebar V3 có biểu trưng cơ khí riêng, nguồn của phiên hiển thị, số khung và khoảng thời gian của bộ đệm. Header có nguồn/chế độ, trạng thái xử lý và điều khiển phiên.
- KPI phía trên vùng quan sát; xu hướng tối đa 90 mẫu lấy trực tiếp từ DashboardState, giữ NaN khi thiếu dữ liệu. Không có chuỗi trang trí sinh ngẫu nhiên.
- Quan sát có overlay keypoint, confidence gốc, cận cảnh/toàn khung, zoom hiển thị 1–2×. Twin đồng bộ EKF, có các bộ phận cơ khí và chiều sâu bản vẽ; không hoạt ảnh khi mất dấu.
- Phân tích có góc quay ba phương pháp, RPM, sai lệch động học, độ bất định và FPS. FPS là nhịp xử lý hiện có, không phải benchmark GPU hoặc độ trễ toàn trình.
- Đánh giá nền, CSV/JSON và phiên video qua decoder → detector dấu màu → EKF; kiểm tra dự báo và mất dấu. Kiểm thử đối chiếu kết quả đánh giá với hàm gốc.
- **60 kiểm thử đạt**, kiểm tra cú pháp đạt. Xem [nhật ký](../assets/dashboard-v3/pytest.txt), [đối chiếu thuật toán](../assets/dashboard-v3/algorithm-audit.txt).
- Hai lượt QA, mỗi lượt 18 ảnh: [offscreen](../assets/dashboard-v3/exact/qa-result.json) và [Windows native](../assets/dashboard-v3/windows/qa-result.json); không phát hiện QLabel bị cắt sau khi hoàn tất layout. Đã xem trực quan ảnh giám sát và phân tích. Các trang còn lại được chụp và kiểm tra bounds tự động, chưa có đợt nghiệm thu thẩm mỹ chuyên sâu V3.

## Chưa được xác minh

- Camera 0 không mở được trên máy QA. Chỉ xác minh kết nối/báo lỗi, chưa xác minh luồng hình ảnh camera vật lý hoặc cơ cấu LEGO thật.
- Chưa có tập dữ liệu LEGO thực được kiểm chứng, trọng số YOLO Pose huấn luyện riêng, benchmark suy luận thực hoặc hiệu chuẩn sai số vật lý.
- Chưa có tham chiếu góc độc lập/encoder cho cơ cấu thật, chưa xác minh MAE/RMSE/bao phủ/độ bất định EKF trên LEGO. Mọi kết quả mô phỏng chỉ kiểm chứng luồng phần mềm.
- Kích thước chính xác 1366×768 và 1920×1080 được kiểm tra bằng offscreen. Windows native có một số cửa sổ yêu cầu 1920×1080 bị giới hạn nội dung thành 1920×1055; xem từng bản ghi JSON.
- V3 là bản bàn giao ổn định trong giới hạn thời gian/hạn mức, **chưa được nghiệm thu là tương đương phần mềm thương mại theo ảnh tham chiếu**. Các khoảng trống và độ lớn cơ cấu còn có thể cải thiện; chưa có chế độ ảnh camera thô tắt overlay hay cửa sổ quan sát tách riêng.
