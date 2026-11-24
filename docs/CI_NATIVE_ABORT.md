# Điều tra native abort Python 3.11

Run PR #2: 43026430257, commit 6e1ec98. Python 3.12/3.13 đạt; 3.11 exit 134 sau 19 dấu chấm. Log không có native message/stack nên chưa xác định nguyên nhân gốc.

Runner dùng Ubuntu 26.04, Python 3.11.18, NumPy 2.4.6, OpenCV contrib 4.14.0.94, PySide6/Shiboken 6.12.0, PyQtGraph 0.14.0, Pillow 13.0.0, pytest 9.2.0. Import QApplication offscreen đã đạt. Không đủ bằng chứng quy lỗi cho plugin Qt hoặc thay phiên bản dependency.

Thứ tự collection đặt test_geometry_file_picker_interaction sau 19 test; test video trước đó và teardown cũng cần xem xét. Số dấu chấm không xác định chắc chắn nơi abort. Giả thuyết gồm vòng đời native widget/worker hoặc tương tác OpenCV–Qt; chưa xác minh.

Máy làm việc là Windows/Python 3.12; Docker Linux daemon chưa chạy, WSL trả E_ACCESSDENIED. Chưa tái hiện Linux/Python 3.11. Test picker riêng đạt 1; nhóm pipeline đạt 13. Chạy full suite verbose/no-capture ban đầu đạt 97 và lỗi encoding CLI do stdout Windows cp1258, không có native abort. Dùng PYTHONUTF8=1 cho chế độ chẩn đoán để tránh nhiễu encoding.

Workflow vẫn chạy toàn bộ test trên cả ba Python. Thêm -X faulthandler, -vv -s, dump stack khi chờ 60 giây, danh sách phiên bản, OpenCV build, NumPy configuration, đường dẫn plugin và hai probe import-order riêng. Nếu suite 3.11 lỗi, chạy picker/dashboard/pipeline thành tiến trình riêng (timeout 180 giây mỗi nhóm), ghi exit code và QT_DEBUG_PLUGINS. Bước suite vẫn giữ trạng thái failure, không được thay bằng kết quả nhóm. Artifact chỉ gồm ci-logs, lưu 7 ngày; không upload core dump hoặc biến môi trường tùy ý.

Đây là commit chẩn đoán có kiểm soát, chưa phải bản sửa nguyên nhân gốc. Dùng artifact của lượt Linux kế tiếp để quyết định thay đổi tối thiểu; không bỏ test, pin dependency tùy đoán hoặc đổi thuật toán/UI.

Kết quả xác minh Windows với PYTHONUTF8=1: toàn bộ 98 test đạt, compileall src/tools đạt. Chưa có kết quả Linux cho commit chẩn đoán.
