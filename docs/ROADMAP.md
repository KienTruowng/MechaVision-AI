# Lộ trình sau bàn giao V4

Baseline giao diện V4 đã chốt; ưu tiên kiểm chứng nghiên cứu, không mở rộng UI khi chưa có nhu cầu đã xác minh.

1. Camera vật lý: quyền truy cập Windows, nguồn hình ổn định, hiệu chuẩn và xử lý mất dấu/phục hồi.
2. Cơ cấu LEGO: đo hình học, thu nhiều phiên độc lập, ghi điều kiện và nguồn gốc dữ liệu.
3. YOLO Pose: nhãn pivot/crank/piston, tách dữ liệu theo phiên, huấn luyện và đánh giá riêng; chưa có trọng số LEGO được xác minh.
4. EKF: tham chiếu góc độc lập, đối chiếu ba phương pháp, sai số/bao phủ/bất định theo phiên; không báo mô phỏng là thực nghiệm vật lý.
5. Máy đích: kiểm tra các mức DPI và màn hình, đo hiệu năng camera/suy luận/render riêng trên RTX 3050 Ti nếu có.

Xem [trạng thái đã kiểm chứng](PROJECT_STATUS.md) và [khôi phục dự án](HANDOFF.md). Không tự push hoặc merge main.
