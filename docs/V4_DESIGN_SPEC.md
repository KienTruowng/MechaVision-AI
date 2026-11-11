# MechaVision AI V4 — Đặc tả thiết kế đã chốt

Ngày chốt: **11/11/2026**. Trạng thái: **quyết định thiết kế để triển khai, chưa phải giao diện đã nghiệm thu**.

## 1. Phạm vi và trạng thái phải giữ lại

- Repository đang làm: `C:\Users\heyim\Documents\Codex\2026-11-09\h-y-l-m-vi-c\work\MechaVision-AI`.
- Nhánh đã kiểm tra: `feature/ultimate-dashboard-v4`. `HEAD`: `902d804833996aacf3b5ea5054314cd0150cbece`. Đây vẫn là commit bàn giao V3; **mã V4 nằm trong các thay đổi chưa commit**, không được suy ra phiên bản ứng dụng chỉ từ `HEAD`.
- Đã đọc `AGENTS.md`, `docs/HANDOFF.md` và các module giao diện liên quan. `HANDOFF.md`, `PROJECT_STATUS.md`, `ROADMAP.md` hiện còn thông tin bàn giao V3. Không làm theo thông tin nhánh cũ để reset hoặc khôi phục đè lên công việc V4.
- Đã xác minh import bằng `.venv\Scripts\python.exe`: `mechavision.gui` trỏ đúng `src\mechavision\gui.py` trong repository này. `run_windows.bat` chuyển về thư mục chứa nó và gọi `.venv\Scripts\python.exe -m mechavision gui`. Việc này xác minh đường khởi động; không chứng nhận mọi cửa sổ Python đã mở trước đó dùng mã mới nhất.
- Lượt chốt thiết kế này chỉ tạo tài liệu này. Không sửa mã UI, reset, commit, chạy ứng dụng, chạy toàn bộ test hoặc xuất ZIP/bundle. Giữ nguyên các thay đổi đang làm, kể cả `twin_renderer.py`, kiểm thử V4 và phần bố cục Analytics đã sửa dở.

## 2. Kết luận từ ảnh tham chiếu và ảnh hiện có

Đã đối chiếu ảnh Sentinex do người dùng cung cấp ngày 11/11, ảnh V3 trong `assets/dashboard-v3/exact/` và ảnh V4 trong thư mục bàn giao `outputs/dashboard-v4/after/exact/` ở workspace. Các ảnh ghép hiện có nằm tại `outputs/dashboard-v4/comparisons/`.

**Điểm cần học từ Sentinex:** vùng quan sát chiếm ưu thế, hình ảnh có độ chi tiết cao, thông tin phụ được tổ chức theo nhóm có mục đích, màu trạng thái tiết chế, tiêu đề và con số có cấp bậc rõ. Không lấy tên, logo, thống kê lỗi sản phẩm, danh sách lỗi, ảnh nhà máy hoặc số liệu của Sentinex vào MechaVision.

**Vấn đề V4 hiện có:** vẫn là dãy KPI ngang trên cùng → hai khung ngang bằng nhau → biểu đồ và bảng nhỏ bên dưới. Sidebar, header và nhịp card gần như V3. Việc thêm màu violet, một KPI và chi tiết cơ khí không thay đổi đủ thứ tự đọc. Tại 1366×768, JSON QA V4 ghi viewport Camera **537×208**, Twin **537×207**: hàng KPI và nhiều lớp toolbar đã lấy mất chiều cao của hai nội dung chính. Ở 1920×1080, hình lớn hơn nhưng vẫn giữ cấu trúc cũ; khoảng trống và vật liệu cơ khí chưa tạo được sự khác biệt đủ rõ.

Ảnh V4 trên là bằng chứng của bản đã chụp, không phải chứng nhận toàn bộ working tree hiện tại: Analytics đã có chỉnh sửa bố cục sau lượt chụp đó. Không dùng số kiểm thử đạt để thay thế nhận xét thiết kế.

## 3. Một hướng thiết kế duy nhất

**Tên định hướng: “Trạm nghiên cứu hai vùng quan sát”.**

Camera và bản sao số là hai dụng cụ quan sát chính, đặt ngay dưới header. Dải dưới là bàn đọc kết quả gồm thông số, xu hướng và trạng thái phiên. Sidebar nhận diện MechaVision V4; header điều khiển phiên. Mắt phải đọc theo thứ tự: **cơ cấu đang quan sát → cơ cấu được ước lượng → con số → diễn biến → chi tiết phiên**.

Quyết định bắt buộc:

1. **Bỏ dãy KPI toàn chiều ngang phía trên Giám sát.** Không được giữ bố cục V3 rồi chỉ trang trí lại.
2. **Camera/Twin chia 56:44**, dùng splitter; không phải hai card 50:50. Cả hai được ưu tiên chiều cao còn lại của cửa sổ.
3. **Dải dưới chia 38:37:25** cho thông số 3×2, xu hướng góc và phiên/sự kiện. Tracking là badge trong header, không chiếm một KPI card riêng.
4. Header, sidebar, card và typography dùng cùng hệ thống dưới đây trên cả bốn trang. Không thêm trang hoặc chức năng nghiên cứu mới để lấp khoảng trống.
5. Hình ảnh cơ khí có vật liệu và chiều sâu bằng phép vẽ 2D có bề dày; không chuyển sang nền tảng 3D hoặc thêm thư viện nặng.

## 4. Bố cục Giám sát và ngân sách kích thước

Các số dưới đây là **pixel logic của vùng client Qt**, không bao gồm thanh tiêu đề Windows hay taskbar. Chúng là ràng buộc layout, không phải tọa độ hard-code cho mọi máy.

```text
┌──────────────────┬─────────────────────────────────────────────────────────┐
│ MechaVision AI   │ Giám sát cơ cấu             Nguồn · AI · Bắt đầu / Dừng │
│ V4 · Nghiên cứu  ├────────────────────────────────┬────────────────────────┤
│                  │ 01  Quan sát thị giác          │ 02  Bản sao số         │
│ Giám sát         │ thanh công cụ gọn              │ điều khiển vùng nhìn   │
│ Phân tích        │                                │                        │
│ Thực nghiệm      │       CAMERA / VIDEO           │   CƠ CẤU CƠ KHÍ LỚN    │
│ Cài đặt          │       + ĐIỂM ĐẶC TRƯNG         │   + TRẠNG THÁI EKF     │
│                  │                                │                        │
│                  │ nguồn · khung · thời gian      │ r · l · e · chú giải   │
│ Phiên hiện tại   ├───────────────────┬──────────────────┬──────────────────┤
│ nguồn / số khung │ Thông số          │ Xu hướng góc     │ Phiên / Sự kiện  │
│ trạng thái       │ 6 ô, lưới 3 × 2   │ 3 phương pháp    │ tóm tắt gọn      │
│                  ├───────────────────┴──────────────────┴──────────────────┤
│                  │ Đường dẫn CSV / trạng thái lưu                         │
└──────────────────┴─────────────────────────────────────────────────────────┘
```

### Hình học chuẩn tại 1366×768

| Thành phần | Kích thước / vị trí mục tiêu |
|---|---|
| Sidebar | Rộng 208; padding 16 |
| Nội dung chính | Rộng 1126; lề trái/phải 16 sau sidebar |
| Header | Cao 64; bắt đầu y=16 |
| Khoảng cách khối | 12 |
| Cặp panel quan sát | y=92; cao 432; Camera 624, Twin 490; khoảng cách 12 |
| Nội dung panel | Header 44; footer kỹ thuật 28; padding 12; khoảng cách tới ảnh đã tính trong header/footer |
| Viewport hữu dụng | Camera khoảng **600×336**; Twin khoảng **466×336** |
| Dải kết quả dưới | y=536; cao 196; ba cột khoảng **419 / 408 / 275** |
| Dòng trạng thái lưu | y=740; cao 16; lề dưới 12 |

Phần header 44 px của mỗi panel chỉ chứa một hàng. Camera: tên ngắn, trạng thái ngắn và nút biểu tượng. Twin: tên ngắn, nút zoom/fit. Nguồn, số khung, thời gian và thông tin mô hình chuyển vào footer; không tái tạo ba hàng caption/toolbar trước hình ảnh.

### Co giãn và Windows DPI

- Tại 1600×900 và 1920×1080: giữ sidebar 208, lề 16, gap 12, header 64 và dải dưới 196. Toàn bộ chiều cao tăng thêm cấp cho cặp panel quan sát. Hero mục tiêu lần lượt cao **564 / 744**. Camera/Twin vẫn 56:44; không phóng lớn chữ theo kích thước màn hình.
- Splitter cho phép điều chỉnh Camera từ 52–60% chiều rộng cặp panel; nút “Vừa khung” chỉ đặt lại phép nhìn, không làm thay đổi dữ liệu hay vị trí splitter. Tỷ lệ mặc định 56:44.
- Với vùng client thấp hơn 740 (ví dụ cửa sổ trên màn hình 1366×768 có titlebar/taskbar): lề 12, gap 8, header 56, dải dưới 168; header/footer panel gọn còn tổng 80. Tính hero từ phần chiều cao thực còn lại; **không đặt footer tại y=740 cố định**. Nhãn đơn vị và tracking không được cắt.
- Nếu DPI làm vùng client rộng dưới 1240: sidebar thu thành rail 76 có icon và nhãn ngắn; không chỉ dựa vào tooltip. Dải kết quả dưới dùng cuộn dọc khi cần. Vùng làm việc rất thấp dưới 680 được cuộn dọc có chủ đích thay vì ép font nhỏ hoặc đè lên điều khiển. Đây là quy tắc thu gọn của cùng bố cục, không phải phương án thiết kế thứ hai.
- Dùng kích thước logic/DPR thực từ Qt, tôn trọng `availableGeometry()`. QA phải phân biệt độ phân giải màn hình, vùng client, kích thước ảnh và DPI. Không buộc cửa sổ vượt màn hình để tuyên bố “vừa 1366×768”.

## 5. Design system dùng chung

### Màu và vật liệu

| Token | Giá trị | Vai trò |
|---|---|---|
| `canvas` | `#070C14` | Nền ứng dụng |
| `sidebar` | `#0A111D` | Điều hướng |
| `surface` | `#101B2B` | Card / bảng / nhóm cấu hình |
| `surface_raised` | `#162338` | Hover, menu, điều khiển nổi |
| `viewport` | `#08131F` | Nền quan sát khi không có ảnh |
| `border` | `#29394E` | Viền mảnh và phân nhóm |
| `text_primary` | `#EDF4FC` | Giá trị và nội dung chính |
| `text_secondary` | `#AABCD1` | Nhãn và đơn vị |
| `text_muted` | `#8194AD` | Metadata không thiết yếu |
| `data_cyan` | `#52D7F1` | EKF vật lý / dữ liệu chính |
| `accent_violet` | `#A696FF` | Điều hướng đang chọn / EKF thời gian |
| `action` | `#6558C7` | Nút chính; hover `#7869DC` |
| `valid` | `#4ED8B2` | Có quan sát được chấp nhận |
| `warning` | `#F1BE62` | Dự báo, thiếu tin cậy, nhãn mô phỏng có chữ |
| `error` | `#F47B87` | Mất dấu / lỗi |

Màu cyan/violet làm điểm nhấn, không phủ tất cả giá trị. Vật liệu Twin dùng thép xám xanh, cạnh sáng và mặt cạnh tối. Không dùng gradient trên nền ứng dụng, glow, glass blur, neon hoặc ảnh trang trí nhà máy. Chỉ cho phép chuyển sắc rất nhẹ trên chi tiết kim loại. Nội dung chữ thường đặt mục tiêu tương phản ít nhất 4,5:1; trạng thái luôn có chữ và biểu tượng, không dựa riêng vào màu.

### Typography, khoảng cách và hình dạng

| Vai trò | Cỡ / độ đậm / chiều cao dòng |
|---|---|
| Tiêu đề trang | 28 / Semibold / 34 |
| Tiêu đề nhóm lớn | 20 / Semibold / 26 |
| Tiêu đề panel | 16 / Semibold / 22 |
| Nội dung / điều khiển | 13 / Regular hoặc Semibold / 20 |
| Metadata / đơn vị / trục | 12 / Regular / 18 |
| Giá trị KPI | 30 / Semibold / 36; thu gọn 26 / 32 |
| Nhãn phụ trong rail thu gọn | 11 / Semibold / 16; không áp dụng cho số đo |

- Phông **Segoe UI**, fallback Noto Sans rồi Arial; tiếng Việt có dấu. Số căn phải hoặc cùng baseline, độ rộng ổn định; không thu nhỏ font theo từng lần cập nhật giá trị.
- Thang spacing duy nhất: **4, 8, 12, 16, 24, 32**. Card padding 12–16; nhóm lớn 24. Border 1 px; radius panel 12, điều khiển 6, badge 4.
- Panel phân lớp bằng màu nền, khoảng cách và đường viền. Không gắn shadow effect vào từng widget; nếu cần, chỉ một bóng tĩnh rất nhẹ ở menu nổi.
- Icon vector 20 px, nét 1,5–1,75 px, cùng kiểu đầu nét bo. Dùng QPainter/SVG trong repo; không emoji và không tải icon font từ mạng.
- Nút thường cao 36; nút biểu tượng vùng nhìn 32×32; focus ring 2 px; vùng bấm tối thiểu 32. Tooltip tiếng Việt, có bàn phím focus. Active/checked khác hover; disabled vẫn đọc được và có giải thích khi cần.

## 6. Sidebar và header

**Sidebar:** logo cơ khí riêng đi cùng chữ **MechaVision AI**, không tiếp tục chữ “MECHA / VISION” chia hai dòng như V3. Bên dưới là dấu phiên bản V4 và nhãn “Trạm nghiên cứu”. Bốn mục điều hướng cao 52, icon 20, tên 14 Semibold; mục chọn dùng mặt nền violet tối, vạch cạnh 3 px và icon sáng. Không thêm menu không hoạt động. Khối phiên ở chân sidebar chỉ có nguồn, số khung và trạng thái thật; không có progress bar nếu chưa biết tổng thời lượng.

**Header:** bên trái tên trang rõ nghĩa (“Giám sát cơ cấu”, “Phân tích dữ liệu”, “Thực nghiệm”, “Cài đặt hệ thống”), dòng phụ “Trạm nghiên cứu · MechaVision AI”. Bên phải nhóm nguồn, trạng thái bộ xử lý, badge tracking và điều khiển Bắt đầu/Dừng; xử lý đang chạy và theo dõi hợp lệ là hai thông tin riêng. Cấu hình là nút icon có tooltip, không tranh ưu tiên với Bắt đầu. Nguồn của phiên đang hiển thị khác nguồn chọn cho phiên kế tiếp; khi dừng phải ghi rõ “Tiếp theo: …”. Không đặt badge tracking lặp lại ở nhiều hàng.

## 7. Camera — vùng quan sát chính

- Ảnh giữ tỷ lệ gốc và căn giữa. Full frame dùng fit/letterbox; cận cảnh dùng miền cố định theo hiệu chuẩn và toàn chu kỳ cơ cấu. Không kéo giãn, không tự bám theo nhiễu keypoint, không crop mất khớp để làm hình trông lớn hơn.
- Toolbar một hàng: bật/tắt điểm và nhãn, cận cảnh/toàn khung, giảm/tăng zoom, fit. Dùng icon và tooltip; chỉ nhãn chế độ đang chọn cần chữ. Zoom/pan/fit là phép biến đổi hiển thị; tắt overlay trả đúng ảnh gốc đã nhận.
- Overlay vector nét 2 px, khớp 5–7 px, nhãn 12–13 px trên nền tối bán trong suốt; chữ không bị scale cùng ảnh. Tránh giao nhau giữa nhãn, giữ nhãn trong viewport. Ba màu điểm cố định: tâm quay bạc, chốt khuỷu cyan, khớp pít-tông violet. Chỉ nối các điểm thực sự hiện có; không tự vẽ điểm quan sát còn thiếu từ EKF.
- Confidence giữ đúng điểm detector/bộ mô phỏng, ghi thang 0–1; không đổi thành “độ chính xác”. Footer ghi khung, thời gian nguồn, số điểm; không thêm thumbnail hoặc ảnh giả làm dữ liệu camera.
- Các trạng thái chờ, kết nối, không có khung, lỗi dùng icon nét và hai dòng hướng dẫn ngắn trong viewport. Khi dừng và giữ ảnh cuối, phải ghi “Đã dừng · Khung cuối”; không để ảnh cũ có vẻ là camera đang trực tiếp.

## 8. Digital Twin — điểm nhấn cơ khí

Chọn **bản vẽ cơ khí chính diện có bề dày giả lập**, giữ mặt phẳng động học đúng tỷ lệ. Không dùng phối cảnh làm sai quan hệ khớp. Cấu trúc hiển thị gồm bệ ổ trục và vòng bạc, trục khuỷu, tay quay có bề dày, thanh truyền có gân/rãnh gia công, hai chốt khớp, pít-tông có rãnh, xi-lanh cắt bổ, ray dẫn hướng và bu-lông liên kết. Bề dày, bu-lông, vật liệu là minh họa, **không phải kích thước thiết kế LEGO đã đo**.

- Thứ tự lớp: nền kỹ thuật rất nhẹ → trục/quỹ đạo → mặt sau và ray → thanh truyền/tay quay/pít-tông → vòng khớp → cạnh sáng → nhãn. Quỹ đạo là đường hình học tĩnh theo cấu hình, không phải dấu vết đo được.
- Chi tiết kim loại: mặt chính xám xanh, mặt cạnh tối, mép sáng 1–2 px, bóng tiếp xúc ngắn 4–8 px. Cyan chỉ nhấn liên kết/khớp; violet nhấn tay quay. Không phủ màu cyan đặc lên toàn cơ cấu.
- Fit tính từ miền bao **toàn chu kỳ** gồm vỏ, ray và biên cơ cấu; dùng một hệ số cho X/Y, tâm hình ổn định. Miền bao chiếm khoảng 80–90% chiều giới hạn của viewport sau khi chừa nhãn. Không đổi scale theo từng góc quay. Với hình học mẫu, cơ cấu phải rõ ngay tại 1366×768, không còn nằm nhỏ giữa một vùng đen lớn.
- Trục X/Y và cung góc nét mảnh; O/C/S ở tâm khớp. Thông tin `r`, `l`, `e` nằm trong footer, đơn vị px; không tự đổi sang mm. Góc trên hình có thể theo chu kỳ 360° để đọc hình, nhưng KPI góc liên tục vẫn giữ nguyên, có nhãn phân biệt.
- Twin chỉ lấy `Geometry` và `Estimate` hợp lệ. Nhãn **“Ước lượng · EKF vật lý”**, thêm nguồn Mô phỏng/Video/Camera riêng. `PREDICTED` ghi “Dự báo”; không gọi Twin là phép đo độc lập. `LOST`/không hữu hạn bỏ tư thế động và hiện lý do, giữ được nền kỹ thuật tĩnh.
- Zoom/fit riêng; không tạo chuyển động nội suy độc lập khi không có mẫu mới, không dùng clock hoạt ảnh để làm đẹp. Tối ưu cache nền/vỏ và render đúng kích thước/DPR; tránh phóng ảnh chữ nhỏ đã raster hóa.

## 9. Dải thông số, biểu đồ và phiên

**Thông số 38%:** một panel, lưới sáu ô 3×2 có đường phân cách mảnh; không sáu card có bóng/viền dày. Nhãn ngắn gắn đơn vị trên một dòng: “Góc quay · °”, “RPM · vòng/phút”, “Sai lệch · px”, “Bất định · °”, “FPS · khung/s”, “Tin cậy · 0–1”. Giá trị 30 px; thiếu dữ liệu là `—`. Không thêm sparkline vào từng ô ở 1366; xu hướng thuộc panel bên cạnh. Header nhóm 28 px, padding 12, gap hàng 8: mỗi ô khoảng 64 px. Số dài được định dạng gọn có tooltip đủ độ chính xác; không cắt chữ số hoặc wrap đơn vị.

Góc, RPM, sai lệch và độ bất định lấy từ kết quả hiện có; FPS là nhịp pipeline hiện có. Confidence tổng hợp dùng điểm nhỏ nhất trong các keypoint hiện hữu, tooltip ghi số điểm n/3; không diễn giải là xác suất đúng. Trạng thái tracking dùng badge, không đặt giá trị giả trong ô bị mất dữ liệu.

**Xu hướng 37%:** góc theo thời gian, 15 giây gần nhất; ba phương pháp cùng màu/kiểu nét trên mọi trang: thị giác trực tiếp amber `#F1BE62` nét 1,5; EKF thời gian violet `#A696FF` nét đứt 1,75; EKF vật lý cyan `#52D7F1` nét liền 2. Legend một hàng ngoài vùng dữ liệu, không che đường. Chỉ 3–4 đường lưới Y rất mờ; không lưới X dày, không làm mượt số liệu. Trục 12 px, đơn vị rõ, giá trị thiếu để đứt đoạn. Cho mở trang Phân tích bằng nút/đường dẫn rõ ràng khi triển khai; không thêm phép tính mới.

**Phiên 25%:** hai tab “Phiên” và “Sự kiện”. Tab Phiên tối đa ba dòng cao 24: điểm quan sát, phép đo nhận/loại, số khung; tracking lấy từ header. Tab Sự kiện là danh sách cuộn của sự kiện thật, không cảnh báo mẫu. Panel rộng khoảng 275 không nhồi đường dẫn dài; đường dẫn CSV đặt ở footer ứng dụng, rút gọn giữa bằng ellipsis và có tooltip đầy đủ. Không tự xuống dòng làm tăng chiều cao footer. Chưa có tệp ghi rõ chưa có tệp.

## 10. Ba trang còn lại cùng một hệ thống

### Phân tích

- Cột thông số phiên bên trái **240 px**, sáu KPI 2×3; nội dung biểu đồ bên phải lấy phần còn lại. Tận dụng phần rail Analytics đã làm dở, chỉnh theo đặc tả, không ghi đè các phương thức dữ liệu.
- Toolbar bộ lọc/so sánh nằm trong vùng biểu đồ, được chia hai hàng ở chiều rộng nhỏ để giữ chữ 13 px. Ba tab: Động học, Chất lượng quan sát, Hiệu năng xử lý.
- Động học: đồ thị góc lớn toàn chiều ngang phía trên; phía dưới chuyển vị và RPM chia 60:40. Độ bất định chuyển vào tab Chất lượng cùng sai lệch và confidence; không bốn biểu đồ nhỏ cạnh nhau với chữ trục dọc quá dài.
- Chất lượng: sai lệch/độ bất định hàng trên 50:50; confidence từng điểm toàn chiều ngang hàng dưới. Hiệu năng: FPS và thời gian xử lý hai đồ thị lớn. `processing_ms` phải ghi đúng phạm vi `Processor.step`; latency toàn trình chưa có thì ghi chưa khả dụng, không suy từ FPS.
- Legend cùng quy tắc; tương tác PyQtGraph giữ nguyên pan/zoom, xuất ảnh/dữ liệu đang hỗ trợ. Empty state có câu hướng dẫn, không vẽ đường minh họa.

### Thực nghiệm

- Bỏ cột cấu hình dọc toàn màn hình. Dùng thanh cấu hình ngang cao khoảng **160 px** ở trên: nguồn đánh giá, nhóm thông số, nơi lưu và nút Chạy. Nhóm CSV/hiệu chuẩn dùng trường chọn tệp thật; cho giãn tới 208 px nếu nguồn đã ghi cần thêm hàng, không ép nhãn.
- Phần dưới: kết quả **70%** (tab biểu đồ/bảng), nhật ký phiên **30%**. Trong cột nhật ký hẹp, trình bày từng phiên thành mục hai dòng có nguồn, thời gian, số khung và trạng thái; dữ liệu vẫn từ lịch sử phiên hiện có. Không ép bảng năm cột vào 330 px.
- Header kết quả gắn nhãn “Mô phỏng” hoặc “Quan sát đã ghi”; ghi rõ điều kiện tham chiếu. Biểu đồ MAE/RMSE/P95 và CSV lấy nguyên báo cáo pipeline; thiếu số liệu để trống, không lấy các con số trong ảnh tham chiếu.

### Cài đặt

- Điều hướng nhóm nội bộ rộng **200 px** bên trái, có tên và mô tả một dòng. Ba nhóm: Nguồn và nhận diện; Hình học và EKF; Hiển thị và lưu trữ. Giữ API `tabs`/trường cấu hình hiện có khi thay cách điều hướng.
- Vùng phải là form có chiều rộng đọc hợp lý, padding 24; nhãn ở trên trường hoặc cột nhãn cố định khi đủ rộng. Các nhóm cao theo nội dung, **không kéo hai card rỗng phủ hết chiều cao** như ảnh V4 hiện có. Phần giải thích dưới nhóm liên quan, không đẩy xuống chân card bằng stretch lớn.
- Nguồn, trọng số, hình học và thiết bị khóa khi chạy; tùy chọn hiển thị áp dụng ngay. Tham số EKF hiện chỉ đọc phải có nhãn “Chỉ đọc”; không tạo slider giả hoặc ngầm đổi mặc định bộ lọc. Thiết lập hiệu năng chưa được hỗ trợ phải ghi rõ, không vẽ điều khiển có vẻ hoạt động.

## 11. Khả thi kỹ thuật và hợp đồng không đổi

- Thực hiện bằng PySide6 Widgets, `QGridLayout`/`QBoxLayout`, `QSplitter`, `QStackedWidget`, `QScrollArea`, QPainter và PyQtGraph đang có. Không đổi framework, không thêm WebView/Qt Quick/engine 3D hay phụ thuộc nặng.
- `dashboard_theme.py`: token duy nhất, bỏ lớp stylesheet ghi đè tích lũy khi hợp nhất. `dashboard_widgets.py`: card/metric/viewport/icon. `dashboard_shell.py`: sidebar/header. Bốn module trang: bố cục tương ứng. `twin_renderer.py`: chi tiết cơ khí và phép nhìn. `gui.py`: nối điều khiển, giữ vòng đời phiên.
- Bảo toàn công việc V4 về `raw_frame`, overlay vector, pan/fit, diagnostics và xuất CSV. Giữ `Worker.sample(frame, twin, data)`, alias UI đang dùng và mọi hợp đồng giữa module. Nhận hai signal ảnh/sample theo đúng cùng khung; overlay không được lệch một khung so với ảnh gốc.
- Không sửa YOLO Pose, EKF, công thức động học, phương pháp đánh giá, đơn vị nội bộ, khóa `Observation`/`Estimate`, thứ tự `pivot/crank/piston` hoặc schema CSV để phục vụ bố cục. Sai lệch động học không được đổi tên thành innovation EKF hoặc chẩn đoán lỗi.
- Thu nhận/suy luận/ước lượng/ghi CSV chạy trên worker hiện có. UI chỉ dựng hình khi cần, không repaint tab ẩn liên tục, không tạo bóng blur trên mỗi frame; cache lớp tĩnh. Không được bỏ mẫu khỏi pipeline/CSV để làm UI mượt. Chưa có số benchmark máy đích thì không ghi hiệu năng được bảo đảm.

## 12. Nghiệm thu bằng hình ảnh ở lượt triển khai

Đây là tiêu chí cho lượt triển khai tiếp theo; **chưa được kiểm chứng trong lượt viết tài liệu này**.

| Cổng nghiệm thu | Điều kiện phải thấy / đo được |
|---|---|
| Đúng phiên bản | Khởi động tiến trình mới từ `.venv` của repository; ghi executable, module path, PID, branch, commit và trạng thái dirty vào biên bản QA. Cửa sổ ghi V4; không dựa chỉ vào tiêu đề |
| Khác bố cục V3 | Không còn KPI hàng đầu; cặp media ngay dưới header; Camera/Twin 56:44; dải dưới ba vùng; sidebar/header mới. Nếu vẫn nhìn như V3 khi thu nhỏ cả hai ảnh còn 50%, chưa đạt |
| Media đủ lớn | Client 1366×768: Camera tối thiểu **580×320**, Twin **450×320**; mục tiêu 600×336 / 466×336. Tổng diện tích hai viewport tăng ít nhất **50%** so với ảnh V4 cũ 537×208 / 537×207 |
| Cơ cấu dễ đọc | Fit miền bao toàn chu kỳ khoảng 80–90% chiều giới hạn; không méo, cắt khớp hoặc nhãn. Ổ trục, tay quay, thanh truyền, pít-tông, vỏ/ray phân biệt được ở ảnh 100% |
| Typography | Nhãn thường ≥13 px, metadata/trục ≥12 px; giá trị KPI 30 px ở bố cục chuẩn. Không cắt dấu tiếng Việt, chữ số, đơn vị, legend hoặc nút |
| Nguồn và trạng thái | Mô phỏng/Video/Camera tách khỏi Tracking/Dự báo/Mất dấu; mất dữ liệu hiện `—` và khoảng trống; không còn tư thế Twin giả đang chạy |
| Cùng design system | Bốn trang dùng cùng header, navigation, màu phương pháp, kiểu tiêu đề, khoảng cách và trạng thái điều khiển |
| Trung thực khoa học | Mọi giá trị truy được về mẫu/báo cáo hiện có; không có cảnh camera, cảnh báo, confidence, biểu đồ hoặc kết quả đo thật dựng sẵn |

Quy trình ảnh bắt buộc cho lượt triển khai:

1. Giữ ảnh V3 và ảnh V4 cũ làm bằng chứng, không ghi đè. Chụp bản redesign vào thư mục QA mới `assets/dashboard-v4/visual-redesign/` khi chuẩn bị bàn giao.
2. Chụp bốn trang ở client **1366×768, 1600×900, 1920×1080**; thêm lượt Windows native với DPI thật và kích thước client khả dụng. Không đổi tên ảnh 1920×1055 thành 1920×1080.
3. So V3/V4 mới cùng client/DPR, cùng cấu hình hình học, chế độ hiển thị và cùng frame mô phỏng có seed để đánh giá kích thước cơ cấu công bằng. Ghi nhãn mô phỏng. FPS là giá trị thời gian chạy nên không yêu cầu bằng nhau và không sửa số cho khớp ảnh.
4. Xem ảnh đầy đủ ở 100% và ảnh ghép 50%; đối chiếu thêm Sentinex về phân cấp, vùng quan sát, nét chữ, mật độ và tính nhất quán. Ảnh tham chiếu chỉ dùng ngoài ứng dụng, không đưa logo hoặc dữ liệu của nó vào sản phẩm.
5. Chụp trạng thái chưa có dữ liệu, mô phỏng hợp lệ, dự báo/mất dấu từ fixture có nhãn, dừng, lỗi nguồn. Nếu camera thật không khả dụng, ghi rõ chưa xác minh, không thay bằng ảnh giả camera.
6. Sửa lỗi hình ảnh trước khi tuyên bố hoàn thiện. Sau đó mới chạy regression tests, cập nhật bàn giao, commit và đóng gói theo yêu cầu triển khai. Test xanh không chứng minh thẩm mỹ; không tuyên bố tương đương Sentinex nếu ảnh chưa đáp ứng các cổng trên.

## 13. Thứ tự triển khai đã khóa

**Shell và token → Giám sát theo ngân sách trên → camera/Twin và KPI → đồng bộ ba trang còn lại → screenshot/đối chiếu/sửa → regression/bàn giao.**

Lượt triển khai tiếp theo bắt đầu bằng `git status`, đọc tài liệu này và giữ các thay đổi đang có. Không quay về V3, không xây lại pipeline, không tách thêm phương án thiết kế. Mục tiêu đầu tiên là ảnh Giám sát 1366×768 đạt các cổng về bố cục và diện tích viewport, rồi mới mở rộng QA và hoàn tất đóng gói. Không merge `main`.

## Trạng thái phát hành 11/11/2026

Baseline bốn trang đã chốt, không redesign trong lượt FINAL QA. 85 test đạt; 84 ảnh QA nằm ở assets/dashboard-v4. Kích thước thực native và giới hạn camera/DPI ghi trong PROJECT_STATUS.md và BAO_CAO_V4.md. Đây là nghiệm thu phần mềm trong môi trường hiện có, không chứng nhận độ chính xác vật lý hoặc chất lượng thương mại.
