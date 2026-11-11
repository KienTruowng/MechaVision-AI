# Biên bản kiểm chứng phần mềm

## Dashboard V2 — 09/11/2026

- `python -m pytest -q`: **53 kiểm thử đạt**, mã thoát 0; giữ toàn bộ 30 kiểm thử trước và thêm 23 trường hợp cho trạng thái, vòng đời phiên, hiển thị và tương tác.
- `python -m compileall -q src tools/verify_dashboard.py`: đạt. Ruff kiểm tra lỗi cú pháp/tên chưa định nghĩa được chọn: đạt. Các module UI mới cũng qua nhóm kiểm tra `F`.
- Đã chạy ứng dụng bằng backend **Windows native**, bắt đầu/dừng mô phỏng, chuyển bốn trang khi đang chạy, thực nghiệm nền và đọc video qua decoder → detector → EKF. Lượt native có 13 ảnh, không có lỗi biên chữ được phát hiện.
- Lượt QA **offscreen** có 16 ảnh, đúng kích thước pixel 1366×768 và 1920×1080, gồm bốn trang và trạng thái chờ, dự báo, mất dấu, kết nối/lỗi camera; không phát hiện nhãn Qt bị cắt. Đã xem trực quan ảnh các trang và các trạng thái bổ sung. Kiểm thử có thêm vùng nội dung 1366×700.
- Trên host DPI 125%, cũng chạy thử native với hệ số tiến trình 0.8 để có DPR 1. Ảnh/biên bản native ghi cả kích thước yêu cầu, kích thước client và kích thước pixel thực; Windows có thể giới hạn chiều cao client theo thanh tiêu đề/taskbar.
- Kiểm tra dữ liệu thiếu không biến thành số không, KPI lấy từ Processor, `LOST` không còn góc/RPM và Digital Twin không chuyển động; tệp ảnh giữ bản sao riêng và tự vẽ lại khi resize.
- Kết quả đánh giá mô phỏng và đánh giá CSV của trang Thực nghiệm trùng với các hàm đánh giá gốc. Đã xác nhận đánh giá chạy ngoài luồng Qt và CSV xuất có tiêu đề Unicode/giá trị số đúng.
- Các tệp động học, EKF, xử lý, dữ liệu, huấn luyện và đánh giá không thay đổi so với `main` làm nền. Các lớp nhận diện và bộ mô phỏng giữ nguyên biểu thức tính toán; chỉ lớp phủ/vẽ hiển thị được nâng cấp.

Camera số 0 **không mở được** trong môi trường kiểm chứng. Đã kiểm tra được trạng thái kết nối, báo lỗi và phục hồi điều khiển; chưa xác minh phép đo camera trên cơ cấu thực. Chưa kiểm chứng huấn luyện/suy luận YOLO với trọng số riêng, độ chính xác vật lý hoặc hiệu năng GPU. Các cảnh video dùng để kiểm tra che khuất là fixture tổng hợp có nhãn rõ ràng, không phải thí nghiệm cơ cấu thực.

Ảnh, kiến trúc, cách sử dụng và lệnh tái lập: [Dashboard V2](DASHBOARD_V2.md). Môi trường thư viện giữ như đợt Việt hóa bên dưới, không thêm phụ thuộc nặng. Hai module kiểm thử Qt yêu cầu nhóm `gui`; môi trường chỉ cài `dev` có thể bỏ qua chúng theo thiết kế.

## Đợt Việt hóa ngày 09/11/2026

Môi trường kiểm tra: Windows, Python **3.12.13**, NumPy **2.5.4**, OpenCV **4.14.0**, Pillow **13.0.0**, PySide6 **6.12.0**, PyQtGraph **0.14.0**. Qt chạy bằng nền tảng **offscreen** để chụp và kiểm tra giao diện mà không cần thiết bị camera.

| Hạng mục | Kết quả |
|---|---|
| `python -m pytest -q` | **30 kiểm thử đạt**: 21 kiểm thử có sẵn và 9 kiểm thử bổ sung |
| `python -m compileall -q src` | Đạt |
| `python -m ruff check src tests/test_localization.py tests/test_gui_localization.py --select F821,F822,F823,E9` | Đạt kiểm tra tên chưa định nghĩa và lỗi cú pháp được chọn; không phải kiểm tra toàn bộ quy tắc định dạng |
| `python -m mechavision simulate --seconds 4` | Tạo được phiên CSV mô phỏng |
| `python -m mechavision evaluate --seconds 24 --fps 30 --seed 42` | Tạo được báo cáo và CSV so sánh ba phương pháp trên mô phỏng |
| `python -m mechavision markers` | Tạo được trang ArUco với nhãn tiếng Việt; kiểm thử nhận diện dấu chuẩn đạt |
| `python -m mechavision demo-video --seconds 2` | Tạo được MP4 có nhãn mô phỏng bằng tiếng Việt |
| `live --no-window --save-video` | Đọc video mô phỏng để thử luồng, ghi được CSV và video có lớp phủ; không phải thử camera thật |
| `extract`, `init-dataset` | Trích được ảnh từ video thử và tạo được cấu trúc dữ liệu, hướng dẫn gán nhãn tiếng Việt |
| Bảng điều khiển Qt | Khởi động, bắt đầu/dừng mô phỏng, đọc hết 60 khung của video thử, cập nhật số liệu/biểu đồ và nhật ký |
| Hiển thị | Kiểm tra ảnh chụp ở cửa sổ 1280×800 và 1450×900; chữ có dấu hiển thị được, bố cục có cuộn khi cửa sổ quá nhỏ |
| Hộp thoại và biểu đồ | Kiểm tra hộp chọn tệp, hộp xuất biểu đồ, nhãn tham số; xuất PNG và CSV UTF-8 thành công |
| Trạng thái | Kiểm tra chưa khởi tạo, đang theo dõi, dự báo và mất dấu; góc/tốc độ để trống khi không có ước lượng hợp lệ |
| Phát lại và đánh giá góc | Bộ kiểm thử đối chiếu ba phương pháp với dữ liệu thử tổng hợp ở định dạng phiên thực và tham chiếu độc lập |

Kiểm thử bổ sung bảo vệ trợ giúp/lỗi tiếng Việt của dòng lệnh, tính toàn vẹn của chữ Unicode trong ảnh BGR, khả năng khởi chạy đúng nguồn mô phỏng sau khi đổi nhãn, cảnh báo thiếu hiệu chuẩn, giá trị lựa chọn xuất CSV và tiêu đề tiếng Việt/giá trị số trong CSV.

Đã đối chiếu cấu trúc cú pháp với phiên bản gốc của các phần tính toán: động học, EKF, nhận diện dấu màu/ArUco/YOLO, mô phỏng, định dạng nhãn, trích/chia dữ liệu và đánh giá. Sau khi bỏ văn bản giải thích/thông báo khỏi phép so sánh, các biểu thức, hằng số số học và toán tử trong các phần này giữ nguyên. Mã trạng thái, khóa dữ liệu và tên điểm tiếp tục được kiểm tra qua các kiểm thử hiện có.

Trong môi trường bị giới hạn quyền ghi, lần chạy pytest ban đầu không tạo được thư mục tạm mặc định. Đã đặt biến môi trường `TEMP` và `TMP` tới một thư mục tạm được phép ghi rồi chạy lại đúng lệnh kiểm thử; không sửa thuật toán để xử lý lỗi môi trường. Khi xuất biểu đồ, đã phát hiện và sửa lỗi bảng mã mặc định Windows bằng bộ xuất CSV UTF-8 trong ứng dụng.

Các lệnh trong bảng được chạy với đường dẫn đầu ra riêng cho dữ liệu kiểm chứng. Không đưa nhật ký hay video sinh tự động vào repository. Hai ảnh trong `assets/` được tạo lại bằng bộ vẽ của dự án để đổi nhãn sang tiếng Việt; cảnh báo trong tệp mẫu mô phỏng được dịch, các số liệu mẫu giữ nguyên.

## Chưa thể xác minh

- Camera/động cơ vật lý, thao tác nhấp hiệu chuẩn và gán nhãn trực tiếp trong cửa sổ OpenCV trên thiết bị của người dùng.
- Độ chính xác đo thực, độ trễ toàn trình/phân vị 95%, FPS trên cơ cấu thực và hiệu năng RTX 3050 Ti.
- Huấn luyện/suy luận YOLO Pose với dữ liệu và trọng số riêng cho động cơ: chưa có dữ liệu thực, nhãn hoặc checkpoint phù hợp; đợt kiểm chứng này không huấn luyện mô hình.
- Giao diện trên mọi hệ điều hành, phông hệ thống, độ phân giải và mức thu phóng màn hình. Ảnh chụp offscreen chưa thay thế kiểm tra trực tiếp trên màn hình đích.
- Thông báo kỹ thuật do thư viện/hệ điều hành tự sinh có thể dùng ngôn ngữ của thư viện/hệ điều hành. Nội dung pháp lý `LICENSE`, các định danh và định dạng trao đổi giữ nguyên.

Biên bản gốc của dự án ghi nhận 21 kiểm thử đạt trên Python 3.13 và chưa chạy được Qt do thiếu phụ thuộc. Kết quả Qt ở trên là kiểm chứng mới trong môi trường được nêu rõ; không suy rộng thành kiểm chứng phần cứng hoặc huấn luyện trên động cơ thực.

**Không dùng kết quả mô phỏng để khẳng định độ chính xác trên cơ cấu thật hoặc khả năng giám sát/chẩn đoán công nghiệp.**
