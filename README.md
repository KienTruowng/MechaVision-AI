# MechaVision AI

**Ước lượng trạng thái bằng thị giác theo thời gian thực cho cơ cấu tay quay–con trượt có ràng buộc vật lý**

MechaVision AI là nguyên mẫu phần mềm phục vụ nghiên cứu và đồ án tốt nghiệp ngành Công nghệ thông tin. Dự án kết hợp thị giác máy tính **OpenCV**, nhận diện điểm đặc trưng bằng **YOLO Pose**, bộ lọc Kalman mở rộng phi tuyến (**EKF**), động học phẳng và bảng điều khiển kỹ thuật **PySide6/PyQtGraph**. Mục tiêu là xây dựng quy trình đo, ước lượng và đánh giá có thể tái lập.

> Repository cung cấp bộ mô phỏng, xử lý camera/video, nhận diện dấu màu/ArUco, tích hợp huấn luyện và suy luận YOLO Pose, gán nhãn thủ công, chia dữ liệu theo phiên, hiệu chuẩn, đánh giá và kiểm thử. **Chưa kèm trọng số nhận diện được huấn luyện riêng trên động cơ thực và chưa có bằng chứng xác minh độ chính xác trên cơ cấu thực.** Kết quả mô phỏng không chứng minh hiệu quả trên động cơ LEGO, tốc độ GPU hay khả năng chẩn đoán hư hỏng công nghiệp. Xem [biên bản kiểm chứng](docs/VALIDATION.md) để phân biệt nội dung đã chạy thử và nội dung chưa xác minh.

## 1. Bài toán và phạm vi nghiên cứu

Hệ thống ước lượng góc trục khuỷu liên tục `theta(t)`, vận tốc góc `omega(t)` và vị trí khớp pít-tông từ quan sát ảnh có nhiễu, che khuất tạm thời và chuyển động quay tay không đều. Ba phương pháp được đối chiếu trên **cùng một luồng quan sát**:

| Phương pháp | Thông tin sử dụng | Mục đích đối chứng |
|---|---|---|
| Thị giác trực tiếp | Chốt khuỷu và tâm quay | Góc tính trực tiếp từ điểm đặc trưng, chưa lọc |
| EKF theo thời gian | Chốt khuỷu và thời gian | Tác động của lọc theo thời gian |
| EKF có ràng buộc vật lý | Chốt khuỷu, khớp pít-tông và thời gian | Tác động của thông tin hình học tay quay–con trượt |

EKF là thuật toán đã biết. Đóng góp cần được kiểm chứng của đồ án là cách áp dụng và đánh giá phép hợp nhất có ràng buộc vật lý cho bài toán thị giác này. Cần báo cáo cả kết quả không cải thiện hoặc kết quả có đánh đổi.

## 2. Kiến trúc và công nghệ

```text
Camera / video → dấu màu / ArUco / YOLO Pose đã huấn luyện ─┐
Nguồn mô phỏng có nhãn, luôn được nhận diện rõ ─────────────┤
                                                          ↓
                                Observation {pivot, crank, piston}
                                      ↓           ↓           ↓
                               Thị giác thô  EKF thời gian  EKF vật lý
                                      └───────────┬───────────┘
                                                  ↓
                                So sánh / độ bất định / trạng thái
                                                  ↓
                         Bảng điều khiển / mô hình số / CSV / đánh giá
```

| Thành phần | Vai trò |
|---|---|
| Python 3.11–3.13; khuyến nghị 3.12 | Ngôn ngữ và môi trường thực thi |
| NumPy | Tính toán ma trận, động học và thống kê |
| opencv-contrib-python | Thu nhận ảnh, dấu màu, ArUco và video |
| Pillow | Vẽ chữ Unicode có dấu lên ảnh/video |
| PySide6, pyqtgraph | Giao diện máy tính và biểu đồ thời gian |
| Ultralytics, PyTorch, PyYAML | Huấn luyện, suy luận và đánh giá YOLO Pose (tùy chọn) |
| pytest, ruff | Kiểm thử và công cụ kiểm tra mã (nhóm `dev`) |

Các module chính:

- `src/mechavision/geometry.py`: hình học tay quay–con trượt có độ lệch ray, đạo hàm giải tích, tọa độ chiếu lên camera.
- `estimators.py`: góc trực tiếp và EKF phi tuyến; hiệp phương sai theo độ tin cậy quan sát, cổng loại ngoại lai, ngừng trả giá trị khi vượt giới hạn bất định.
- `detection.py`, `acquisition.py`: nhận diện và thu nhận camera/video.
- `dataset.py`, `train.py`: trích ảnh, gán nhãn, chia theo phiên, huấn luyện và đánh giá điểm đặc trưng.
- `evaluation.py`, `real_ablation.py`, `real_evaluation.py`, `replay.py`: đánh giá mô phỏng và đối chiếu dữ liệu đã ghi với tham chiếu độc lập.
- `gui.py`, `processing.py`, `render.py`, `i18n.py`: giao diện Qt, luồng xử lý, hiển thị và nhãn tiếng Việt.
- `session.py`, `tests/`: nhật ký CSV và kiểm thử tự động.

Xem [kiến trúc chi tiết](docs/ARCHITECTURE.md) và [bảng thuật ngữ, khóa dữ liệu](docs/TERMINOLOGY.md).

## 3. Cài đặt trên Windows

Cài Python 3.12 và Git, tải mã nguồn rồi mở PowerShell trong thư mục `MechaVision-AI`:

```powershell
git clone https://github.com/KienTruowng/MechaVision-AI.git
cd MechaVision-AI
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
.venv\Scripts\python.exe -m mechavision gui
```

Có thể chạy `install_windows.bat` để cài đặt, sau đó nhấp đúp `run_windows.bat` để mở ứng dụng. Thông báo của các tệp `.bat` dùng UTF-8. Ảnh/video cần phông Unicode như Segoe UI trên Windows, DejaVu Sans/Noto Sans trên Linux hoặc Arial trên macOS. Mã nội bộ, tên tệp, API, tham số dòng lệnh và khóa CSV/JSON vẫn giữ nguyên để tương thích.

Để huấn luyện hoặc suy luận YOLO, cài thêm:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[train]"
```

Nhóm `train` có thể cài PyTorch chỉ dùng CPU. Nếu dùng NVIDIA RTX 3050 Ti 4 GB, xem [hướng dẫn cài đặt PyTorch chính thức](https://pytorch.org/get-started/locally/) để chọn bản tương thích CUDA. Có thể bắt đầu với YOLO-nano, ảnh 640, `batch` bằng **4**, giảm xuống **2** nếu thiếu bộ nhớ GPU; đây là cấu hình khởi đầu, không phải kết quả đo hiệu năng. Dùng `--device cpu` khi chạy bằng CPU.

## 4. Chạy mô phỏng và sử dụng bảng điều khiển

```powershell
.venv\Scripts\python.exe -m mechavision gui
```

Chọn **Nguồn → Mô phỏng**, sau đó **Bắt đầu phân tích**. Giao diện gồm ảnh quan sát, mô hình động học số, góc, tốc độ vòng/phút, độ bất định của góc, sai lệch vị trí theo mô hình và biểu đồ thời gian. Phiên được lưu vào `outputs/session_*.csv`.

Nguồn dữ liệu và chất lượng theo dõi là hai thông tin riêng:

| Nhãn hiển thị | Ý nghĩa |
|---|---|
| Dữ liệu mô phỏng | Dữ liệu tổng hợp, không phải phép đo động cơ thực |
| Đo camera trực tiếp | Quan sát từ camera; phụ thuộc hiệu chuẩn và cách bố trí khớp |
| Phân tích video đã ghi | Xử lý tệp video; người dùng phải xác minh nguồn gốc video |
| Chưa khởi tạo (`UNINITIALIZED`) | Cần quan sát chốt khuỷu để bắt đầu |
| Đang theo dõi (`TRACKING`) | Có phép đo được bộ lọc chấp nhận |
| Đang dự báo (`PREDICTED`) | Dự báo ngắn hạn, không có phép đo mới được chấp nhận |
| Mất dấu (`LOST`) | Quá thời gian dự báo hoặc vượt giới hạn bất định; góc và tốc độ để trống |
| Không đủ độ tin cậy | Không có ước lượng hợp lệ để hiển thị; không kết luận hỏng cơ khí |

Nhãn “đang theo dõi” không phải bảo đảm độ chính xác ngoài thực tế. Độ bất định là kết quả của mô hình bộ lọc, cần kiểm chứng hiệu chuẩn riêng. Khi phiên kết thúc, giá trị còn trên màn hình là mẫu cuối cùng.

Chạy không cần giao diện:

```powershell
.venv\Scripts\python.exe -m mechavision simulate --seconds 12
.venv\Scripts\python.exe -m mechavision evaluate --seconds 24 --fps 30 --noise 3 --out outputs/ablation
.venv\Scripts\python.exe -m pytest -q
```

Lệnh `evaluate` tạo `summary.json` và `ablation.csv`. **Mô phỏng chứng minh luồng phần mềm chạy được, chưa kiểm chứng cơ cấu vật lý.** Có thể dùng `demo-video` để xuất MP4 mô phỏng; xem `python -m mechavision --help` và trợ giúp từng lệnh.

## 5. Kết nối camera và hiệu chuẩn

Hai phương pháp dùng dấu chuẩn hoạt động trước khi huấn luyện AI:

- **Dấu màu** (`color`): đỏ = tâm quay cố định, xanh lá = chốt khuỷu, xanh dương = khớp thanh truyền–pít-tông. Tâm nhãn phải trùng tâm khớp mô hình.
- **ArUco** (`aruco`): ID `0` = tâm quay, `1` = chốt khuỷu, `2` = khớp pít-tông. Hệ thống chưa tự động hiệu chỉnh độ lệch giữa tâm dấu chuẩn và tâm khớp thực.

```powershell
.venv\Scripts\python.exe -m mechavision markers --out assets/aruco_markers.png
.venv\Scripts\python.exe -m mechavision calibrate --source 0 --out configs/geometry.json
.venv\Scripts\python.exe -m mechavision live --source 0 --detector color --geometry configs/geometry.json
```

Hiệu chuẩn bằng bốn lần nhấp: **(1)** tâm quay `O`, **(2)** chốt khuỷu `C`, **(3)** khớp pít-tông–thanh truyền thực `S`, **(4)** điểm xác định chiều dương trục trượt. Nhấn **Enter** để lưu, **R** để đặt lại, **Esc** để hủy. Camera cần cố định, gần vuông góc với mặt phẳng chuyển động. Bộ hiệu chuẩn từ chối hình học không phù hợp với cơ cấu tay quay–con trượt cứng.

Trong bảng điều khiển, chọn **Camera trực tiếp** hoặc **Video đã ghi**, nhập nguồn, chọn tệp `configs/geometry.json` đã hiệu chuẩn và bộ nhận diện tương ứng. `configs/geometry.example.json` chỉ là cấu hình ví dụ, không phải hiệu chuẩn cơ cấu thực. Tùy chọn YOLO Pose cần tệp trọng số đã huấn luyện.

Cơ cấu khác mô hình hoặc khớp pít-tông không nhìn thấy không thể được xem là đã hỗ trợ đo chính xác nếu chưa thay đổi và kiểm chứng mô hình vật lý.

## 6. Thu thập dữ liệu và huấn luyện AI

Thu ít nhất ba phiên ghi **độc lập**; nên có nhiều phiên với ánh sáng, tốc độ quay tay, khoảng dừng, đảo chiều và mức che khuất khác nhau:

```powershell
.venv\Scripts\python.exe -m mechavision record --out data/raw/session01.mp4 --seconds 30
.venv\Scripts\python.exe -m mechavision record --out data/raw/session02.mp4 --seconds 30
.venv\Scripts\python.exe -m mechavision record --out data/raw/session03.mp4 --seconds 30
```

Trích ảnh, gán nhãn và chia dữ liệu **theo phiên quay**, không trộn ngẫu nhiên các khung hình liền kề:

```powershell
.venv\Scripts\python.exe -m mechavision extract --video data/raw/session01.mp4 --session session01 --stride 8
.venv\Scripts\python.exe -m mechavision extract --video data/raw/session02.mp4 --session session02 --stride 8
.venv\Scripts\python.exe -m mechavision extract --video data/raw/session03.mp4 --session session03 --stride 8
.venv\Scripts\python.exe -m mechavision annotate --folder data/labeled/session01
.venv\Scripts\python.exe -m mechavision annotate --folder data/labeled/session02
.venv\Scripts\python.exe -m mechavision annotate --folder data/labeled/session03
.venv\Scripts\python.exe -m mechavision split --root data/labeled --out data/pose_dataset
```

Thứ tự ba điểm là `pivot` (tâm quay), `crank` (chốt khuỷu), `piston` (khớp pít-tông). Với `annotate --folder`: **nhấp trái** chọn điểm, **S** bỏ qua điểm bị che, **R** đặt lại, **Enter** lưu và chuyển ảnh, **Q** thoát. Khung hình không thấy điểm nào không được lưu nhãn. Không gán điểm suy diễn/không nhìn thấy như quan sát thực.

Đường gán nhãn trực tiếp `annotate --video` dùng bộ phím khác: **1/2/3** chọn điểm, **nhấp trái** đặt điểm, **nhấp phải** xóa điểm, **S** lưu, **N** bỏ qua khung, **Q** thoát. `init-dataset` tạo cấu trúc `dataset.yaml` cho đường này; phải tự tách phiên huấn luyện/xác thực và dành phiên kiểm tra độc lập. Quy trình `extract → annotate --folder → split` ở trên tạo đủ train/val/test và `data.yaml` tự động. **Lệnh `split` tạo lại thư mục đầu ra**, vì vậy không dùng thư mục chứa dữ liệu gốc làm `--out`.

Huấn luyện và kiểm tra (có thể cần mạng để tải trọng số khởi tạo `yolo11n-pose.pt`):

```powershell
.venv\Scripts\python.exe -m mechavision train --data data/pose_dataset/data.yaml --model yolo11n-pose.pt --epochs 80 --batch 4 --device 0
.venv\Scripts\python.exe -m mechavision validate --data data/pose_dataset/data.yaml --weights runs/mechavision/pose/weights/best.pt --split test --device 0
.venv\Scripts\python.exe -m mechavision keypoint-eval --data data/pose_dataset --weights runs/mechavision/pose/weights/best.pt --split test --device 0
```

Ultralytics có thể tăng số thứ tự thư mục lần chạy; kiểm tra đường dẫn `best.pt` thực tế. Mô hình tư thế người có sẵn không nhận diện được các điểm cơ khí riêng này nếu chưa tinh chỉnh. Khi đã có trọng số phù hợp:

```powershell
.venv\Scripts\python.exe -m mechavision live --source 0 --detector yolo --weights runs/mechavision/pose/weights/best.pt --geometry configs/geometry.json --device 0
```

Giao diện, trợ giúp và thông báo do dự án định nghĩa dùng tiếng Việt. Thông báo kỹ thuật do Python, Qt, OpenCV, Ultralytics hoặc PyTorch tự sinh có thể theo ngôn ngữ thư viện/hệ điều hành; không sửa mã thư viện để dịch chúng.

## 7. Thuật toán

Với bán kính tay quay `r`, chiều dài thanh truyền `l`, độ lệch ray `e`, tọa độ khớp pít-tông theo chiều dương trục trượt là:

\[x(\theta)=r\cos\theta+\sqrt{l^2-(e-r\sin\theta)^2}.\]

Trạng thái `s = [theta, omega]` dùng mô hình vận tốc cục bộ không đổi kèm nhiễu quá trình gia tốc. EKF dự báo tọa độ chốt khuỷu và, khi bật ràng buộc vật lý, tọa độ khớp pít-tông. Đạo hàm giải tích tạo ma trận quan sát; độ tin cậy điểm điều chỉnh nhiễu đo; cổng sai lệch đổi mới loại ngoại lai; hiệp phương sai cập nhật theo dạng Joseph. Không trả góc/tốc độ khi quá giới hạn bất định hoặc thời gian dự báo.

EKF theo thời gian dùng cùng mô hình quá trình và cấu hình nhiễu nhưng bỏ phép đo pít-tông. So sánh này tách ảnh hưởng của thông tin hình học bổ sung. Các phép tính nội bộ dùng pixel, giây, radian và radian/giây; giao diện đổi sang độ và vòng/phút. Chi tiết giả thuyết, công thức và thiết kế thí nghiệm nằm trong [quy trình nghiên cứu](docs/RESEARCH_PROTOCOL.md).

## 8. Thực nghiệm và đánh giá

Thu góc tham chiếu độc lập bằng phép đo thủ công đã kiểm tra hoặc encoder vật lý; **không dùng chính EKF đang đánh giá**. Mẫu định dạng ở `samples/reference_angles_TEMPLATE.csv`:

```csv
frame,theta_deg
1,17.5
2,22.2
3,27.1
```

Các số trên chỉ minh họa định dạng, không phải số liệu thực nghiệm. Cố định tham số trước khi kiểm tra và cho ba bộ ước lượng dùng **cùng các quan sát đã lưu**:

```powershell
.venv\Scripts\python.exe -m mechavision real-ablation --session outputs/live_session.csv --ground-truth data/reference_angles.csv --geometry configs/geometry.json --out outputs/real_ablation
```

Kết quả gồm `summary.json`, `real_ablation.csv`, MAE, RMSE, phân vị 95% sai số góc và tỷ lệ có ước lượng hợp lệ. Khi có nhóm khung hình chốt khuỷu bị che nhưng pít-tông còn nhìn thấy, báo cáo có tỷ lệ bao phủ riêng. Sai số được quy theo chu kỳ 360°; chỉ số này chưa xác minh được số vòng quay liên tục. Dùng dữ liệu tham chiếu thực sự độc lập và ghi rõ nguồn gốc, phương pháp đo, sai số tham chiếu.

Đánh giá một bộ ước lượng:

```powershell
.venv\Scripts\python.exe -m mechavision evaluate-real --session outputs/live_session.csv --ground-truth data/reference_angles.csv --out outputs/real_evaluation.json
```

Các kiểm thử phát lại dùng dữ liệu tổng hợp ở định dạng phiên thực chỉ xác minh logic phần mềm. Tệp `samples/synthetic_benchmark.json` là kết quả mô phỏng lưu sẵn, không phải phép đo động cơ thực và không tự cập nhật theo mỗi lần chạy.

## 9. Giới hạn khoa học và vận hành

1. Phải xác minh cơ cấu thực là tay quay–con trượt phẳng lý tưởng, điểm nhận diện trùng khớp mô hình và phép chiếu phù hợp. Nếu chưa xác minh, chưa có kết luận đo cơ cấu thực.
2. Chưa kèm trọng số riêng cho động cơ. Dấu màu/ArUco là phương pháp đối chứng hợp lệ, không thay thế kết quả học sâu.
3. EKF hai trạng thái giả định vận tốc cục bộ không đổi. Che khuất dài có thể làm mất số vòng/nhập nhằng pha; khi đó hệ thống phải ngừng trả giá trị đáng tin cậy. Gần điểm chết, thông tin góc từ pít-tông có thể yếu hoặc nhập nhằng.
4. Camera phải cố định. Góc nhìn xiên, phối cảnh và sai số đặt dấu chuẩn cần hiệu chuẩn bổ sung; chưa có tự động hiệu chỉnh homography hoặc nội tại camera trong luồng hiện tại.
5. Độ chính xác tuyệt đối, độ trễ, FPS, độ bền vững và hiệu năng RTX 3050 Ti cần đo trên thiết bị đích với thí nghiệm được kiểm soát. Dừng/đảo chiều khi quay tay là chuyển động bình thường, không phải dấu hiệu hỏng máy.
6. Đây là nguyên mẫu nghiên cứu có thể chạy, chưa phải sản phẩm giám sát công nghiệp được chứng nhận hoặc hệ thống chẩn đoán lỗi cơ khí.

## 10. Kiểm thử và chất lượng mã nguồn

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m compileall -q src
```

Các tệp dữ liệu, trọng số và kết quả sinh tự động được tách khỏi mã nguồn; xem `.gitignore`. Phạm vi kiểm chứng và các giới hạn chưa được xác minh được ghi trong [biên bản kiểm chứng](docs/VALIDATION.md).

Giấy phép mã nguồn: **MIT**; giữ nguyên văn bản pháp lý trong `LICENSE`. Kiểm tra riêng giấy phép của thư viện và trọng số mô hình.
