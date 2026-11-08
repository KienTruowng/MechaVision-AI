# Lộ trình sau bàn giao V3

Thực hiện theo nhu cầu và dữ liệu được cung cấp; đây là công việc dự kiến, không phải kết quả đã đạt.

1. **Xác minh camera và LEGO:** mở camera trên máy đích, cố định gá, xác định đúng tâm quay/chốt khuỷu/khớp pít-tông, đo hình học và kiểm tra mất dấu/dừng/chuyển nguồn. Lưu phiên có nguồn gốc, điều kiện chiếu sáng, góc nhìn và phiên bản hiệu chuẩn.
2. **Thu thập dữ liệu:** quay các phiên LEGO độc lập với tốc độ, chiều quay, ánh sáng và mức che khuất khác nhau. Tách train/val/test theo phiên, không chia các khung gần nhau vào nhiều tập. Không dùng ảnh/video tổng hợp QA làm dữ liệu đo thật.
3. **YOLO Pose:** gán nhãn đúng thứ tự ba điểm; kiểm tra chất lượng nhãn và tệp cấu hình, huấn luyện bằng công cụ hiện có. Ghi trọng số, seed, cấu hình, phiên bản thư viện và nguồn dữ liệu; đánh giá keypoint trước khi thay detector dấu màu.
4. **Tham chiếu và EKF:** xây dựng góc tham chiếu độc lập (encoder hoặc gán nhãn đã kiểm tra); đồng bộ số khung/thời gian. So sánh thị giác trực tiếp, EKF thời gian và EKF vật lý trên cùng quan sát; báo cáo MAE, RMSE, P95, bao phủ và lỗi cả khi không cải thiện. Chỉ điều chỉnh mô hình/nhiễu bằng phiên xác thực, giữ test độc lập.
5. **Thực nghiệm:** kiểm tra ảnh hưởng hiệu chuẩn, tốc độ, che khuất, chuyển động thuận/ngược và độ bất định; báo cáo số phiên, số mẫu, mẫu thiếu/loại bỏ, phần cứng, thời gian chạy. Không suy diễn chẩn đoán hư hỏng từ residual.
6. **Nghiệm thu UI V3:** khi có hạn mức mới, so ảnh với tiêu chí phân cấp/thông tin/khả năng đọc của thiết kế tham chiếu; ưu tiên cơ cấu lớn hơn ở 1366×768 và tiết giảm khoảng trống. Dùng dữ liệu xử lý thật hoặc mô phỏng có nhãn; không thêm metric giả để tạo hiệu ứng thị giác.
7. **GitHub:** dùng bundle bàn giao hoặc nhánh local đã kiểm tra; sau khi người dùng cung cấp đường xác thực phù hợp, cập nhật nhánh và mở PR để review. Không tự merge main.

Chi tiết quy trình nghiên cứu: [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md). Trạng thái thực tế: [PROJECT_STATUS.md](PROJECT_STATUS.md).
