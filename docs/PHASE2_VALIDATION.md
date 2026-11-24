# Phase 2.1 — readiness, 11/11/2026

Nhánh `feature/phase2-real-vision`, tiếp tục từ `f305060`. Không redesign V4, không đổi YOLO Pose/EKF/kinematics/renderer hoặc cột CSV. Bản V4 gốc vẫn là `fe235e5`.

- Thu nhận từ chối ảnh rỗng/sai định dạng, giải phóng handle khi lỗi; timestamp video lặp sau giá trị hợp lệ không còn tiến chỉ 1 microsecond mỗi khung.
- Watchdog UI: quá 15 giây không tiến triển sẽ báo lỗi và yêu cầu stop; chặn mẫu đến muộn. Pause và pacing cập nhật heartbeat nên không gây timeout giả. Đóng cửa sổ khi đang thu nhận không wait trên UI thread; chờ signal finished trước đóng. Không terminate worker/driver. Timeout cũng có thể xảy ra khi tải mô hình/suy luận rất chậm; cần kiểm chứng máy đích.
- Hiệu chuẩn dùng cùng FrameSource với dashboard (camera yêu cầu 960×540, kích thước thực do driver quyết định). Lưu geometry JSON tương thích và `.calibration.json` chứa kích thước ảnh, hash geometry, đơn vị và tỷ lệ mm tùy chọn. Worker từ chối ảnh khác kích thước hoặc geometry thay đổi sau hiệu chuẩn; cấu hình cũ thiếu sidecar vẫn đọc được nhưng không xác minh độ phân giải.
- Mỗi phiên dashboard có `.metadata.json` cạnh CSV: nguồn, detector/device, geometry snapshot, độ phân giải nguồn, thời gian UTC và thời gian quan sát, số khung/trạng thái tracking, kết thúc/lỗi. `simulation` hoặc `unverified_capture`; camera/video không tự được chứng nhận vật lý. Không có ground truth thì accuracy chưa khả dụng, latency là null. Sidecar không sửa schema đánh giá hiện có.
- Cleanup luôn phát tín hiệu kết thúc kể cả lỗi lưu/đóng. Metadata cập nhật lúc khởi tạo, biết kích thước nguồn và kết thúc; nếu tiến trình bị kill, trạng thái running không phải kết thúc thành công. Không ghi metadata mỗi frame để tránh I/O không cần thiết.

Kiểm chứng: 50 test liên quan đạt; 3 test Windows native đạt (2 test chạy lại + 1 test mới, tổng 51 test khác nhau). Compileall src/tools đạt. Native bao gồm video fixture có đổi tốc độ/che khuất/phục hồi, pause/resume/stop và capture giả lập bị chặn: UI còn phản hồi, close không chờ đồng bộ, hủy hợp tác rồi đóng tài nguyên. Lần chạy đầu có 1 test timestamp thất bại do sai lệch 1 microsecond; đã sửa logic và nhóm 50 test chạy lại đạt. Không chạy toàn bộ QA dashboard.

Chưa xác minh LEGO/camera vật lý/YOLO riêng/GPU/latency toàn trình. Chưa có dữ liệu ground truth để công bố MAE/RMSE/P95 vật lý. Driver bị chặn vẫn có thể giữ worker đến khi read/open trả về; không thể bảo đảm cưỡng chế đóng mọi backend Windows. Không claim kiểm thử rò rỉ bộ nhớ dài hạn. Confidence marker là trọng số quy ước/điểm hình dạng, không phải độ chính xác đã hiệu chuẩn.


## Chạy hiệu chuẩn và demo Phase 2.1

Từ repository:

```powershell
.venv\Scripts\python.exe -m mechavision calibrate --source "data/raw/lego_session01.mp4" --out configs/lego_session01.json
.venv\Scripts\python.exe -m mechavision gui
```

Trong cửa sổ hiệu chuẩn nhấp O, C, S rồi một điểm xác định chiều dương trục trượt tính từ O; Enter lưu, R chọn lại, Esc hủy. Điểm thứ tư không nhất thiết nằm trên ray. Nhãn sai/hình học không khả thi bị từ chối, có thể chọn lại. Camera dùng `--source 0`. Không suy kích thước LEGO từ tên bộ hoặc ảnh minh họa.

Chọn Video/Camera và tệp `configs/lego_session01.json` trong Cài đặt, dùng đúng góc máy/độ phân giải khi hiệu chuẩn. Không đổi zoom camera quang học hoặc vị trí camera sau hiệu chuẩn. Giữ `.calibration.json` cùng geometry khi di chuyển cấu hình.

Thông số hình học có thể nhập qua Geometry JSON: radius_px, rod_px, origin_x/y, slider_offset_px là pixel; axis_deg là độ. Geometry kiểm tra hữu hạn, bán kính dương và điều kiện quay toàn vòng. EKF nội bộ dùng radian, UI hiển thị độ/RPM. Không nhập mm trực tiếp vào trường `_px`. Khi đã đo tỷ lệ độc lập, có thể dùng `save_calibration(geometry, output, (width, height), mm_per_pixel=...)`; tỷ lệ chỉ là metadata, không đổi đơn vị thuật toán hoặc trục dashboard. Không có tỷ lệ mặc định. Giả thiết mặt phẳng/góc nhìn và sai số click vẫn cần xác minh trên vật lý.

Độ chính xác: dùng tham chiếu độc lập và real_ablation có sẵn; các số MAE/RMSE/P95 chỉ hợp lệ với dữ liệu tham chiếu đã kiểm tra đồng bộ và đơn vị. FPS/processing_ms hiện có không đại diện latency camera→màn hình. Ghi nguyên video, cấu hình, metadata và CSV mỗi phiên; không đổi tên fixture tổng hợp thành dữ liệu thực.

Kiểm thử readiness: `python -m pytest -q tests/test_phase21_readiness.py tests/test_phase2_pipeline.py`. Capture bị chặn trong test là giả lập có thể giải phóng, không chứng minh driver thật luôn hủy được. Nút tạm dừng giữ mẫu cuối; mất điểm không bổ sung điểm suy luận vào cột obs_*; mất nguồn chuyển lỗi và bỏ mẫu đến muộn.

---

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
