# Quy trình nghiên cứu

## Câu hỏi và giả thuyết có thể kiểm chứng

**Câu hỏi nghiên cứu:** Việc bổ sung ràng buộc phép đo có ý nghĩa vật lý của cơ cấu tay quay–con trượt vào bộ ước lượng thị giác theo thời gian có cải thiện tái dựng góc trên các phiên video thực **chưa từng dùng để huấn luyện/tinh chỉnh**, khi có nhiễu, che khuất một phần và tốc độ biến thiên hay không?

- **H1:** EKF có ràng buộc vật lý giảm MAE/RMSE góc so với cùng EKF chỉ dùng chốt khuỷu trên dữ liệu giữ lại.
- **H2:** Khi tạm mất quan sát chốt khuỷu nhưng còn quan sát pít-tông, phương pháp tăng tỷ lệ có trạng thái hợp lệ mà không làm sai số tăng quá mức.
- **H3:** Ràng buộc bổ sung không làm tăng đáng kể độ trễ toàn trình; cần đo để kết luận.

**Giả thuyết không:** không cải thiện hoặc đánh đổi kém hơn trong cùng điều kiện. Phải báo cáo trung thực cả kết quả âm tính.

## Mô hình toán học

Với tay quay–con trượt lý tưởng có độ lệch ray, bán kính đo được `r`, chiều dài thanh truyền `l`, độ lệch `e`, vị trí khớp pít-tông theo chiều dương trục trượt là:

\[x(\theta)=r\cos\theta+\sqrt{l^2-(e-r\sin\theta)^2}.\]

Trạng thái \(s_t=[\theta_t,\omega_t]^T\) tiến triển theo mô hình vận tốc cục bộ không đổi cộng nhiễu gia tốc Gaussian:

\[s_{t+1}=\begin{bmatrix}1&\Delta t\\0&1\end{bmatrix}s_t+w_t.\]

Hàm quan sát dự báo vị trí ảnh của chốt khuỷu và, trong mô hình ràng buộc, khớp thanh truyền–pít-tông từ cùng trạng thái. `estimators.py` thực hiện dự báo EKF, sai lệch đổi mới, cổng loại ngoại lai và cập nhật hiệp phương sai dạng Joseph. Đối chứng theo thời gian dùng **cùng mô hình quá trình, lựa chọn nhiễu và phép đo chốt khuỷu**, nhưng bỏ phép đo pít-tông để tách ảnh hưởng của thông tin hình học bổ sung. Đối chứng trực tiếp suy góc từ chốt quay so với tâm quay.

Áp dụng hàm quan sát hình học đã biết không đồng nghĩa với phát minh thuật toán tối ưu mới. Đóng góp học thuật cần dựa trên cách thích nghi với bài toán thị giác được chọn và bằng chứng từ nghiên cứu có đối chứng.

## Thiết kế thực nghiệm

- Dùng từ ba phiên thu nhận độc lập trở lên cho mỗi điều kiện; thay đổi góc bắt đầu, tốc độ, ánh sáng. Không để phiên quay xuất hiện đồng thời trong train/val/test.
- Các điều kiện: bình thường; đổi ánh sáng; đổi tốc độ/đảo chiều; che chốt khuỷu nhưng thấy pít-tông; che pít-tông nhưng thấy chốt khuỷu; che cả hai để kiểm tra khả năng ngừng trả ước lượng.
- Thu góc khuỷu và độ bất định tham chiếu bằng phép đo độc lập cho các khung được chọn. Không dùng giá trị thật của bộ mô phỏng trong thí nghiệm cơ cấu thực.
- Thu nhãn pixel độc lập cho tâm quay, chốt khuỷu, khớp thanh truyền–pít-tông. Báo cáo chất lượng nhận diện AI và sai lệch điểm riêng với chất lượng ước lượng trạng thái.
- Đo MAE/RMSE/phân vị 95% sai số góc, tỷ lệ có dự báo hợp lệ, dự báo bị coi là hợp lệ sai khi che khuất, độ trễ camera → kết quả, phân vị 95% độ trễ, FPS, RAM và VRAM. Có thể phân tích hiệu chuẩn độ bất định.
- Phân biệt sai số góc theo chu kỳ 360° với sai số **đếm vòng liên tục**; sai số theo chu kỳ không xác minh số vòng.
- Cho cả ba bộ ước lượng dùng cùng luồng phép đo trong thí nghiệm ghép cặp. Ước lượng khoảng tin cậy bootstrap theo **phiên**, không coi các khung hình liền kề là mẫu độc lập.
- Chỉ chỉnh ngưỡng/tham số bằng dữ liệu huấn luyện và xác thực; cố định trước lần kiểm tra cuối.

## Giới hạn và trường hợp thất bại

- Mô hình tay quay–con trượt lệch tâm chỉ áp dụng khi đúng động học cơ cấu. Cần xem xét bánh răng, bộ phận không phẳng và vị trí khớp pít-tông trước khi đưa ra kết luận.
- Phép chiếu camera RGB cần hiệu chuẩn; xấp xỉ gần trực giao 2D không luôn đúng với góc nhìn xiên. Homography là hướng mở rộng.
- Khi che chốt khuỷu gần điểm chết, hiệu chỉnh góc từ pít-tông có thể yếu hoặc nhập nhằng. Theo dõi đa giả thuyết là hướng phát triển, chưa phải khả năng đã có.
- Dừng/đảo chiều động cơ quay tay **không phải hư hỏng**. Hệ thống cung cấp độ nhất quán với mô hình và chất lượng theo dõi, chưa chẩn đoán lỗi công nghiệp.
- Kết quả mô phỏng chỉ kiểm tra vận hành phần mềm, không chứng minh thành công của bộ nhận diện đã huấn luyện hoặc thí nghiệm vật lý.

## Các mốc triển khai

1. Xác minh điểm nhìn thấy rõ và hình học trên thiết bị thực; loại hình học không phù hợp.
2. Thu dữ liệu, thiết lập nhãn độc lập và quy trình đo tham chiếu.
3. Xây dựng, huấn luyện mạng điểm đặc trưng riêng; đối chiếu OpenCV/ArUco khi thích hợp.
4. Đánh giá EKF theo thời gian và EKF vật lý trên cùng quan sát đã lưu.
5. Hoàn thiện vận hành thời gian thực, bảng điều khiển và nhật ký; đo hiệu năng máy đích.
6. Lặp thí nghiệm, phân tích lỗi và viết luận văn kèm lệnh tái lập, kết quả và giới hạn.
