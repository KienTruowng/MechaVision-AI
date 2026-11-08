# Thuật ngữ và quy ước dữ liệu

Giao diện và diễn giải dùng tiếng Việt. Định danh Python, tham số dòng lệnh, giá trị lựa chọn và khóa CSV/JSON giữ nguyên để các module, kiểm thử và công cụ phân tích tiếp tục tương thích.

| Thuật ngữ / định danh | Diễn giải thống nhất |
|---|---|
| Slider–crank | Cơ cấu tay quay–con trượt |
| `pivot` | Tâm quay cố định |
| `crank` | Chốt khuỷu |
| `piston` | Khớp pít-tông–thanh truyền, không phải một điểm tùy ý trên thân pít-tông |
| Keypoint / landmark | Điểm đặc trưng, tương ứng tâm khớp vật lý |
| Marker | Dấu chuẩn (dấu màu hoặc thẻ ArUco) |
| Ground truth | Giá trị tham chiếu độc lập; mô phỏng có giá trị thật riêng |
| EKF | Bộ lọc Kalman mở rộng |
| Innovation | Sai lệch đổi mới giữa phép đo và dự báo |
| Outlier gating | Cổng loại phép đo ngoại lai |
| Ablation | So sánh loại bỏ thành phần để đánh giá tác động của thành phần đó |
| Digital twin | Mô hình động học số; hình vẽ từ ước lượng, không phải cảm biến độc lập |
| Confidence | Độ tin cậy do bộ nhận diện gán cho điểm; không phải xác suất đúng đã hiệu chuẩn |
| Uncertainty | Độ bất định do bộ lọc ước lượng, cần kiểm chứng hiệu chuẩn riêng |
| Train / val / test | Huấn luyện / xác thực / kiểm tra; tách theo phiên quay |

## Trạng thái nội bộ

| Mã | Nhãn hiển thị | Cách hiểu |
|---|---|---|
| `UNINITIALIZED` | Chưa khởi tạo | Chưa có quan sát chốt khuỷu để khởi tạo bộ lọc |
| `TRACKING` | Đang theo dõi | Có phép đo được chấp nhận |
| `PREDICTED` | Đang dự báo | Dự báo ngắn hạn, không có phép đo mới được chấp nhận |
| `LOST` | Mất dấu | Vượt giới hạn độ bất định hoặc thời gian dự báo; không trả góc/tốc độ |

Nhãn nguồn dữ liệu được hiển thị riêng. Mô phỏng vẫn có thể ở trạng thái “đang theo dõi”; trạng thái này không biến dữ liệu tổng hợp thành phép đo thực.

## Khóa nhật ký và chỉ số

| Khóa | Ý nghĩa / đơn vị |
|---|---|
| `frame`, `time_s` | Mã khung hình và thời gian (giây) |
| `theta_rad`, `omega_rad_s` | Góc liên tục (rad), vận tốc góc (rad/s) |
| `rpm` | Tốc độ vòng/phút; có dấu để biểu thị chiều quay |
| `sigma_deg`, `sigma_theta_rad` | Độ lệch chuẩn góc (độ hoặc rad theo tên khóa) |
| `fit_residual_px` | Độ lớn trung bình sai lệch đổi mới của phép đo được chấp nhận (pixel) |
| `kinematic_discrepancy_px` | Chênh lệch vị trí pít-tông quan sát và dự báo từ góc chốt khuỷu (pixel) |
| `obs_*_x`, `obs_*_y`, `obs_*_conf` | Tọa độ ảnh và độ tin cậy của từng điểm |
| `truth_rad_synthetic_only` | Góc thật chỉ do mô phỏng tạo; không dùng làm tham chiếu thực |
| `mae_deg` | Trung bình sai số tuyệt đối của góc (độ) |
| `rmse_deg` | Căn trung bình bình phương sai số góc (độ) |
| `p95_abs_error_deg` | Phân vị 95% của sai số góc tuyệt đối |
| `coverage_pct`, `availability_pct` | Tỷ lệ có ước lượng hợp lệ trên khung tham chiếu/khung mô phỏng của báo cáo tương ứng |
| `recall` | Tỷ lệ điểm phát hiện được trên tổng điểm tham chiếu nhìn thấy |
| `pck_at_threshold` | Tỷ lệ điểm trong ngưỡng sai số, tính có điều kiện trên các điểm đã phát hiện |
| `raw_cv_baseline`, `raw_visual` | Hai tên báo cáo hiện có cho đối chứng thị giác trực tiếp |
| `temporal_ekf`, `physics_ekf` | EKF theo thời gian, EKF có ràng buộc vật lý |

Ô trống trong nhật ký là giá trị thiếu, không phải số không. Các chỉ số góc theo chu kỳ 360° không xác minh độ chính xác đếm vòng liên tục. Những giá trị số trong tệp mẫu mô phỏng không phải số liệu đo động cơ thực.
