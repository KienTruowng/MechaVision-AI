# Phase 2 — luồng camera/video và giao thức kiểm chứng

Ngày 11/11/2026. Nhánh `feature/phase2-real-vision`, nền V4 `fe235e577fae160b26da793e419e133537d4ec94`. Giữ nguyên thiết kế V4, YOLO adapter, Geometry, EKF, Processor và schema CSV/JSON.

## Phần đã triển khai

- `acquisition.py`: giải phóng handle khi không mở được nguồn; camera thử lại tối đa hai lần khi mất khung, sau đó báo lỗi thay vì xem là EOF video; timestamp video lặp/không hợp lệ dùng frame/FPS dự phòng.
- `dashboard_controller.py`: tạm dừng/tiếp tục có thể ngắt bằng stop; video phát theo chênh lệch timestamp thay vì chờ cố định 20 ms. Video giữ vị trí khi tạm dừng; camera đọc và bỏ khung để hạn chế tồn đọng bộ đệm. Không tự nội suy quan sát thiếu.
- `gui.py`: tái sử dụng nút Bắt đầu phiên thành Tạm dừng/Tiếp tục khi đã nhận dữ liệu; Dừng vẫn kết thúc phiên. Không đổi layout. UI giữ mẫu cuối với nhãn tạm dừng; không tiếp tục chuyển động Twin.
- Camera/video → detector dấu màu/ArUco hoặc YOLO có trọng số → Observation → ba estimator → Twin và CSV tiếp tục chạy trên worker, không chạy suy luận trên UI thread.
- Tọa độ detector vẫn từ ảnh gốc; zoom/pan chỉ đổi hiển thị. Pít-tông thiếu để trống trong CSV; trạng thái ước lượng không được điền vào cột quan sát.

## Kiểm thử thực hiện

60 test liên quan đạt, 0 thất bại (gồm 5 test mới). Hai test vòng đời/video chạy lại bằng Qt Windows native: 2 đạt. Compileall src/tools đạt. Không chạy lại toàn bộ QA dashboard hoặc toàn bộ suite.
Fixture MJPG 90 khung, 30 FPS đi qua OpenCV decoder và ColorMarkerDetector thực: giai đoạn đủ điểm, che pít-tông, che toàn bộ, phục hồi. Test kiểm tra PREDICTED/LOST/TRACKING, Twin tạo ảnh, CSV đủ 90 hàng, quan sát bị che để trống, theta rỗng khi LOST, tạm dừng/tiếp tục/dừng an toàn và nhịp phát. Đây là video **tổng hợp kiểm thử**, không phải LEGO thật. Test camera dùng capture giả lập để kiểm tra mất khung và đóng handle.

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_phase2_pipeline.py
.venv\Scripts\python.exe -m mechavision gui
```

Trong Cài đặt: chọn Video, tệp của bạn, hình học đã hiệu chuẩn và detector phù hợp; bắt đầu phiên. Dùng nút Tạm dừng/Tiếp tục tại vị trí nút Bắt đầu. Dừng trước đổi nguồn.
Camera: chọn Camera trực tiếp, chỉ số 0 hoặc camera thích hợp và hình học đúng độ phân giải khung thu nhận. Dấu màu: đỏ O, xanh lá C, xanh dương S. ArUco: ID 0/1/2. Đặt tâm dấu đúng khớp hoặc hiệu chỉnh sai lệch gá đặt.
CPU fallback: chọn Dấu màu/ArUco (không cần GPU), hoặc đặt thiết bị YOLO `cpu` với trọng số đã huấn luyện. Không tự tải trọng số hoặc tự chuyển CUDA sang CPU khi lỗi; dừng phiên, chọn CPU rồi chạy lại. Chưa kiểm thử YOLO thật vì thiếu trọng số LEGO.

## Giao thức LEGO có thể lặp lại

1. Cố định camera gần vuông góc mặt phẳng chuyển động; lưu độ phân giải, FPS, ánh sáng, khoảng cách, thông số camera và hình học từng phiên. Không dùng geometry.example.json làm hiệu chuẩn thật.
2. Thu nhiều phiên tốc độ thấp/vừa/cao trong phạm vi thiết bị. Ghi video gốc, thời gian, phiên và điều kiện; không resize sau hiệu chuẩn nếu không chuyển đổi geometry tương ứng.
3. Dùng encoder hoặc nhãn góc độc lập với bộ detector đang đánh giá. Lưu sai số tham chiếu, cách đồng bộ frame và quy ước góc liên tục/radian; không lấy EKF hay hình vẽ Twin làm ground truth. Sau mất dấu dài, số vòng tuyệt đối có thể không quan sát được.
4. Tách phiên huấn luyện/xác thực/kiểm thử; giữ nguyên tập kiểm thử. So sánh thị giác trực tiếp, EKF thời gian và EKF vật lý trên cùng quan sát bằng pipeline real_ablation hiện có. Kiểm tra định dạng đầu vào bằng `python -m mechavision --help` và tài liệu đánh giá trước chạy.
5. Thử che riêng O/C/S, che toàn bộ với thời lượng ghi lại, thay đổi ánh sáng và nhiễu; báo cáo thời gian mất dấu/phục hồi, độ bao phủ bên cạnh MAE/RMSE/P95. Không bỏ các khung mất dấu khỏi mẫu số độ bao phủ.
6. FPS hiện tại là nhịp Processor nhận mẫu; processing_ms chỉ thời gian Processor.step. Đo latency camera→hiển thị riêng bằng đồng hồ/hình ảnh tham chiếu đồng bộ, công bố điểm bắt đầu/kết thúc và phân bố độ trễ. Không suy latency từ 1/FPS. Chưa có số latency vật lý trong lượt này.
7. Lưu cấu hình, commit, phiên bản phần mềm, dữ liệu gốc và báo cáo CSV/JSON để người khác tái lập. Confidence dấu màu là điểm hình dạng, ArUco là trọng số quy ước, YOLO là confidence mô hình; không phải xác suất đúng đã hiệu chuẩn.

## Giới hạn còn lại

Chưa xác minh camera thật/LEGO/YOLO riêng/RTX 3050 Ti. OpenCV read/open phụ thuộc driver: retry hữu hạn không bảo đảm timeout nếu chính driver chặn trong read; UI vẫn chạy nhưng đóng ứng dụng có thể phải chờ worker. Không dùng terminate ép luồng vì dễ hỏng tài nguyên. Camera không tự kết nối lại: sửa nguồn rồi bắt đầu phiên mới.
Tạm dừng có thể hoàn tất một mẫu đang xử lý vào CSV; UI ngừng nhận mẫu mới ngay. Video không tua/lặp. EOF không phân biệt chắc chắn tệp hỏng và hết tệp. Sau tạm dừng camera, timestamp giữ thời gian thực và có khoảng trống; cần kiểm chứng EKF phục hồi trên cơ cấu thật chuyển động trong khoảng trống. Không khẳng định số vòng tuyệt đối được bảo toàn khi không quan sát được.
