# Làm việc với MechaVision AI trên GitHub

Repository: [KienTruowng/MechaVision-AI](https://github.com/KienTruowng/MechaVision-AI).

## Tải và chạy mã nguồn

```powershell
git clone https://github.com/KienTruowng/MechaVision-AI.git
cd MechaVision-AI
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
.\.venv\Scripts\python.exe -m mechavision gui
.\.venv\Scripts\python.exe -m pytest -q
```

Cài Python 3.12 và Git nếu máy chưa có. Bản clone đã có `.git`; không chạy lại `git init`. Nếu nhận gói ZIP có lịch sử `.git` và remote đã cấu hình, có thể kiểm tra trước khi đẩy:

```powershell
git remote -v
git push -u origin main
```

Đây là lệnh đẩy trực tiếp vào `main` của quy trình xuất bản ban đầu. Với thay đổi mới trên repository đang phát triển, ưu tiên nhánh riêng như bên dưới. Không tải toàn bộ mã nguồn dưới dạng một tệp ZIP duy nhất nếu muốn công cụ đọc và kiểm tra từng tệp.

## Gửi thay đổi qua Pull Request

```powershell
git switch -c docs/viet-hoa-mechavision
git status
git add README.md docs src
git commit -m "docs: Việt hóa giao diện và tài liệu MechaVision AI"
git push -u origin docs/viet-hoa-mechavision
```

Kiểm tra danh sách tệp và thêm chính xác các tệp khác cần thiết trước khi commit. Mở Pull Request từ nhánh mới vào `main` trên GitHub, mô tả thay đổi, kết quả kiểm thử và các nội dung chưa xác minh. Đăng nhập khi Git Credential Manager hoặc trình duyệt yêu cầu. Không đưa dữ liệu, trọng số, bí mật hay kết quả sinh tự động vào commit ngoài chủ đích; xem `.gitignore`.

`tools/publish_github.ps1` dành cho xuất bản ban đầu bằng GitHub CLI: cần `gh auth login`, đúng tài khoản `KienTruowng`, mặc định tạo repository **riêng tư** khi kho chưa tồn tại. Script có thể đổi tên nhánh thành `main` và đẩy mã, vì vậy không dùng thay cho quy trình nhánh/Pull Request ở trên.

## Trạng thái nghiên cứu

Chưa kèm trọng số YOLO Pose được huấn luyện trên động cơ LEGO thực. Chưa có kết quả kiểm chứng từ camera và góc tham chiếu độc lập trên cơ cấu của người dùng. Demo là mô phỏng, không phải kết quả đo máy thực.
