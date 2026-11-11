# Kiến trúc phần mềm

Phiên bản đang phát triển: Dashboard V4, nền V3 `902d804`. Xem [trạng thái](PROJECT_STATUS.md), [báo cáo V4](../BAO_CAO_V4.md) và [hướng dẫn tiếp tục](HANDOFF.md). Pipeline nghiên cứu dưới đây được bảo toàn; UI không sửa quan sát, trạng thái ước lượng hoặc công thức để phục vụ hiển thị.

```text
Camera vật lý / video đã ghi            Nguồn mô phỏng có thể tái lập
              └──────────────────┬──────────────────┘
                                 ↓
                       Khung hình + thời gian
                                 ↓
             ColorMarkerDetector / ArucoDetector / YOLOPoseDetector
                     hoặc quan sát mô phỏng có nhiễu
                                 ↓
                    Observation {pivot, crank, piston}
                 ┌───────────────┼───────────────────┐
                 ↓               ↓                   ↓
       RawVisualEstimator     MotionEKF           MotionEKF
                          (physics=False)      (physics=True)
                 └───────────────┼───────────────────┘
                                 ↓
                 Phép đo, độ bất định, trạng thái theo dõi
                 ┌───────────────┼───────────────────┐
                 ↓               ↓                   ↓
          Bảng điều khiển Qt    Nhật ký CSV      Đánh giá ngoại tuyến
          Mô hình động học số                  + tham chiếu độc lập
```

## Quy ước và trách nhiệm các thành phần

- Đơn vị nội bộ: vị trí **pixel**, thời gian **giây**, góc **radian**, vận tốc góc **rad/s**. Giao diện đổi sang độ và vòng/phút.
- `Geometry`: khớp cứng vật lý, phép chiếu, độ lệch ray và hàm chuyển vị khả vi.
- `MotionEKF`: cập nhật quan sát phi tuyến, cổng loại ngoại lai theo sai lệch đổi mới và cập nhật hiệp phương sai dạng Joseph. `physics=False` loại phép đo pít-tông. Khi tâm quay tạm vắng, dùng tâm quan sát gần nhất hoặc tâm đã hiệu chuẩn; camera phải cố định.
- `SessionWriter`: ghi CSV liên tục; phép đo thiếu để trống. Giá trị thật của bộ mô phỏng nằm riêng trong `truth_rad_synthetic_only`, không dùng làm tham chiếu thực.
- `dataset.py`: một đối tượng cơ cấu, đúng **ba điểm** theo thứ tự `pivot` / `crank` / `piston`. Đường `initialize_dataset` dùng tên lớp `slider_crank_mechanism`; đường `split_by_session` dùng `mechanism`; cả hai đều là lớp số 0. Không đổi tên lớp hoặc thứ tự điểm khi Việt hóa.
- `gui.py`: điều phối vòng đời phiên và bốn trang của Dashboard V4, giữ điểm vào `launch()` và signal `Worker.sample(frame, twin, data)`.
- `dashboard_controller.py`: các `QThread` sở hữu camera/nhận diện/ước lượng/nhật ký hoặc gọi nguyên hàm đánh giá. Signal bổ sung `raw_frame` truyền bản sao ảnh trước lớp phủ để UI bật/tắt annotation mà không sửa hợp đồng `sample`, khóa dữ liệu hoặc đầu vào detector. Luồng Qt sở hữu biểu đồ và vẽ giao diện; không chạy suy luận hay đánh giá trên luồng giao diện.
- `dashboard_state.py`: bộ đệm hiển thị 3.600 mẫu từ kết quả `Processor`; không ghi đè phép đo thiếu bằng số không. Nhật ký CSV vẫn ghi toàn bộ phiên qua `SessionWriter`.
- `dashboard_theme.py`, `dashboard_widgets.py`, `dashboard_shell.py`: design system, component và khung điều hướng. BrandMark tự vẽ, Sparkline từ tối đa 90 mẫu thực sự nhận được; zoom/pan/fit chỉ đổi phép biến đổi vẽ ảnh. Các module trang `dashboard_monitoring.py`, `dashboard_analytics.py`, `dashboard_experiments.py`, `dashboard_settings.py` tách riêng không gian sử dụng. Lịch sử thiết kế: [Dashboard V2](DASHBOARD_V2.md), [V2.1](DASHBOARD_V2_1.md).
- `render.py`/`twin_renderer.py`: bản vẽ cơ khí từ `Geometry` và `Estimate`, dùng tọa độ đồng tỷ lệ. Vật liệu, bóng và phần vỏ chỉ là biểu diễn; tâm khớp và chuyển vị lấy đúng mô hình hiện có. V4 không bổ sung mô phỏng động lực học hoặc thời gian hoạt ảnh riêng.
- `i18n.py`: ánh xạ nhãn tiếng Việt và vẽ Unicode trên ảnh BGR bằng Pillow. Không thay mã trạng thái, tên điểm hoặc khóa dữ liệu. Ưu tiên Segoe UI/DejaVu Sans/Noto Sans/Arial; cần cài một phông hỗ trợ tiếng Việt trên hệ điều hành.
- `real_evaluation.py`: ghép dự báo phiên và góc tham chiếu độc lập theo số khung hình; báo cáo mẫu số của tỷ lệ bao phủ. Người thực nghiệm chịu trách nhiệm nguồn gốc và tính độc lập của tham chiếu.

## Trạng thái và nguồn dữ liệu

`TRACKING` → Đang theo dõi; `PREDICTED` → Đang dự báo; `LOST` → Mất dấu; `UNINITIALIZED` → Chưa khởi tạo. Mã trong CSV và giữa các module giữ nguyên. Khi mất dấu, không hiển thị góc/tốc độ và báo không đủ độ tin cậy. Nhãn nguồn mô phỏng, camera trực tiếp hoặc video đã ghi hiển thị riêng; tệp video không tự được xem là dữ liệu cơ cấu thực đã kiểm chứng.

## Công việc cần hoàn thành trước bảo vệ

1. Xác minh gá đặt, hình học và vị trí khớp từ ảnh/video cơ cấu thực.
2. Huấn luyện YOLO Pose trên động cơ mục tiêu; repository chưa kèm trọng số này.
3. Xây dựng tham chiếu thủ công/encoder độc lập và kiểm tra nhãn góc.
4. Bổ sung homography và hiệu chuẩn nội tại camera nếu góc nhìn yêu cầu.
5. Kiểm chứng hiệu chuẩn độ bất định và chỉnh nhiễu gia tốc bằng các phiên xác thực.
6. Đo hiệu năng trên máy đích; cân nhắc ONNX khi có nhu cầu thực tế.
7. Hoàn thiện so sánh loại bỏ thành phần trên dữ liệu thực và khoảng tin cậy theo phiên.
