# CHECKPOINT TIẾN ĐỘ — Module Thử Kính Ảo (Virtual Try-On)

> File này được tạo ngay trước khi di chuyển project từ
> `D:\ĐH CNTT\Học kì 3\PythonProject\ChuyenDeTN` sang `D:\ChuyenDeTN`
> (lý do: MediaPipe crash khi đường dẫn có dấu tiếng Việt — xem mục 5).
> Đọc file này đầu tiên khi mở lại phiên làm việc mới để tiếp tục đúng mạch,
> không cần khảo sát lại từ đầu.

---

## 1. Yêu cầu ban đầu của người dùng

Xây dựng module **thử kính ảo qua webcam thời gian thực** cho website TMĐT bán kính
mắt (Django + MySQL), tích hợp vào đồ án tốt nghiệp. Toàn bộ yêu cầu chi tiết nằm
trong file **`PROMPT_VirtualTryOn_ClaudeCode.md`** (đã có sẵn trong repo, không sửa).

Tóm tắt các điểm cốt lõi:

- Pipeline bắt buộc (xử lý từng khung hình): **OpenCV** thu khung hình → **OpenCV**
  chuẩn hoá ánh sáng (CLAHE/gamma) → **MediaPipe Face Mesh** nhận diện landmark +
  head pose → **OpenCV** biến đổi + alpha-blend PNG kính lên mặt → hiển thị lên
  trình duyệt.
- **Bài toán A (trọng tâm chấm điểm)**: chống độ trễ/giật lag khi xử lý real-time.
- **Bài toán B**: xử lý outlier — nghiêng mặt 3/4, đeo khẩu trang, che khuất một
  phần, thiếu sáng — dựa vào độ tin cậy nhận diện để ẩn/hiện kính + gợi ý tiếng Việt.
  KHÔNG tự train lại model, chỉ dùng đúng MediaPipe pre-trained + graceful
  degradation.
- Quy trình 5 giai đoạn, làm tuần tự, dừng lại xin duyệt sau mỗi giai đoạn:
  1. Nghiên cứu & khảo sát (không code)
  2. Prototype độc lập (`prototype/tryon_demo.py`, chưa tích hợp Django, đo FPS)
  3. Giải quyết Bài toán A (đo FPS trước/sau từng kỹ thuật tối ưu)
  4. Giải quyết Bài toán B (script kiểm thử outlier)
  5. Tích hợp vào Django (app riêng, không phá vỡ chức năng hiện có)
- Người dùng là sinh viên, ưu tiên code dễ hiểu, comment tiếng Việt giải thích *tại
  sao*, giải pháp đơn giản hơn giải pháp phức tạp, giải thích trước khi code, nói
  thẳng nếu có gì sai kỹ thuật thay vì làm theo mù quáng.

**Trạng thái quy trình (2026-07-31): Giai đoạn 2 đã được người dùng duyệt
trực quan. Đang ở mục 11 — Bước 1 (ghép PNG kính thật), code đã xong + tự
test xong (không cần webcam), đang CHỜ người dùng tự chạy webcam thật để
canh 2 số `width_ratio`/`vertical_offset` bằng phím rồi duyệt trực quan**
trước khi sang Bước 2 (Giai đoạn 3 — tối ưu độ trễ). Xem mục 12 để biết chi
tiết đầy đủ và lệnh chạy chính xác; mục 9 là log Giai đoạn 2 gốc (đã xong,
không cần đọc lại để tiếp tục).

---

## 2. Quyết định đã thống nhất với người dùng (KHÔNG hỏi lại)

| # | Quyết định | Lý do |
|---|---|---|
| 1 | Xử lý ảnh ở **server (Python, Django backend)**, không xử lý client-side JS thuần | Đề cương yêu cầu cụ thể OpenCV+MediaPipe (Python); xử lý client-side sẽ triệt tiêu "Bài toán A" (không còn độ trễ mạng để giải quyết) |
| 2 | Transport giữa trình duyệt và server: **WebSocket qua Django Channels** (không dùng HTTP polling lặp lại mỗi frame) | Chuẩn ngành cho video AI real-time, tránh overhead header/CSRF/middleware lặp lại mỗi frame ở tần suất 15-30fps |
| 3 | Ảnh PNG nền trong suốt của kính: **model mới `GlassesOverlay`** (OneToOne → `Product`) trong **app mới `tryon`**, KHÔNG sửa model `ProductImage` hiện có | Tránh đụng vào app `products` đang chạy ổn định với 441 ảnh thật; giữ đúng nguyên tắc tách app riêng |
| 4 | Môi trường Python: **venv riêng trong chính thư mục project** (không dùng chung venv ở `PythonProject/.venv`) | Venv ở `PythonProject/.venv` là môi trường công cụ chung (jupyter, pandas, graphify...), không phải venv của Django project này |
| 5 | Đổi đường dẫn project sang **không dấu**: `D:\ChuyenDeTN` (thay vì `D:\ĐH CNTT\Học kì 3\PythonProject\ChuyenDeTN`) | MediaPipe Tasks API crash cứng khi CWD/đường dẫn chứa ký tự tiếng Việt có dấu — xem chi tiết mục 5 |
| 6 | MediaPipe API: dùng **Tasks API mới** `mediapipe.tasks.python.vision.FaceLandmarker` (KHÔNG dùng `mp.solutions.face_mesh` như chữ trong đề cương gốc) | Đã kiểm chứng thực tế: bản mediapipe mới nhất (0.10.35) đã **xoá hẳn** `mp.solutions` — API cũ không còn tồn tại, không phải giả định |

### Điểm đã sửa sai so với tài liệu gốc (đã báo cho người dùng)

- `PROMPT_VirtualTryOn_ClaudeCode.md` dòng 107 giả định *"đang dùng Bootstrap"* —
  **SAI**. Dự án cố tình **không dùng Bootstrap/jQuery/framework ngoài** (xem
  `static/css/style.css` dòng đầu: tránh phụ thuộc CDN/internet). UI module mới
  phải viết bằng CSS thuần + vanilla JS theo đúng style hiện có.

---

## 3. Hiểu biết về codebase (đã khảo sát kỹ ở Giai đoạn 1 — KHÔNG cần khảo sát lại)

Project Django tên `core`, 5 app: `accounts`, `products` (lõi), `cart`, `wallet`
(model xong, view/url còn placeholder), `favorites` (tương tự wallet — đã đổi
tên từ `wishlist` ở phiên 2026-07-31, xem mục 10).

**Route/template quan trọng cho module try-on:**
- Route chi tiết sản phẩm: `products:detail` → `products/san-pham/<slug>/`
- Template: `templates/products/detail.html` (extends `base.html`) — nơi gắn nút
  "Thử kính ảo"
- Model `Product` (app `products`, file `products/models.py`): có field `image`
  (ImageField, `.jpg`), `category` (FK → `Category`, 10 dáng gọng: Aviator,
  Cat-Eye, Round, Square, D-Frame, Oval, Rectangle, Octagon, Shield, Wrap),
  `price`, `stock_quantity`, `gender`, `specs` (JSONField), `slug`
- Model `ProductImage` (`related_name="images"`): ảnh gallery `.jpg`, field
  `image` (`upload_to="products/gallery/"`), `position`
- **Chưa có ảnh PNG nền trong suốt nào** trong 441 ảnh hiện có (toàn bộ ảnh chụp
  thật crawl từ lespecs.com) → cần asset PNG riêng cho AR (xem quyết định #3)

**Hạ tầng:**
- `core/settings.py`: MySQL qua PyMySQL (giả `MySQLdb`), `STATIC_URL="static/"`,
  `STATICFILES_DIRS=[BASE_DIR/"static"]`, `MEDIA_ROOT=BASE_DIR/"media"`,
  `TEMPLATES.DIRS=[BASE_DIR/"templates"]`, `AUTH_USER_MODEL="accounts.User"`
- **Không có Channels/ASGI thực sự** (file `core/asgi.py` chỉ là boilerplate mặc
  định) → khi làm Giai đoạn 5 cần tự thêm `channels` vào `INSTALLED_APPS`, cấu
  hình `ASGI_APPLICATION`, `CHANNEL_LAYERS` (dùng `InMemoryChannelLayer` — đủ cho
  1 tiến trình demo, không cần Redis)
- `static/css/style.css` (1678 dòng, thuần CSS), `static/js/main.js` (166 dòng,
  vanilla JS) — không Bootstrap, không jQuery, không SPA
- `requirements.txt` (trước khi thêm gói mới): `Django==4.2.23`,
  `PyMySQL==1.2.0`, `python-dotenv==1.2.2`, `Pillow==12.3.0`, `requests==2.34.2`
- **Không có file `.gitignore`** trong repo — cần tạo mới ở Giai đoạn 5 (ít nhất:
  `.env`, `__pycache__/`, `*.pyc`, `staticfiles/`, `.venv/`, và cân nhắc file
  model MediaPipe `.task` nếu không muốn commit binary nặng)
- Python 3.13.14, không Docker

---

## 4. Môi trường & package — TRẠNG THÁI SAU KHI DI CHUYỂN PROJECT

**Quan trọng: venv cũ đã bị XOÁ** (ở `D:\ĐH CNTT\...\ChuyenDeTN\.venv`) trước khi
di chuyển, vì venv gắn chặt với đường dẫn tuyệt đối (di chuyển sẽ hỏng do
`pyvenv.cfg` và shebang trong `Scripts/*.exe` chứa path cũ). **Phải tạo lại venv
tại vị trí mới `D:\ChuyenDeTN`.**

### Việc cần làm ngay khi mở lại tại `D:\ChuyenDeTN` (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install opencv-python mediapipe
```

Các bản đã xác nhận hoạt động tốt cùng nhau (đã test trước khi xoá venv cũ):
- `opencv-python` → `cv2.__version__` = **5.0.0**
- `mediapipe` → `mp.__version__` = **0.10.35**
- `numpy` → **2.5.1**

`requirements.txt` **chưa được cập nhật** với `opencv-python`/`mediapipe` (theo
đúng kế hoạch, việc này chính thức thuộc Giai đoạn 5 theo tài liệu gốc — nhưng cần
cài thủ công ngay bây giờ để chạy prototype Giai đoạn 2).

### Model MediaPipe đã tải sẵn

File **`prototype/models/face_landmarker.task`** (~3.6MB) đã tải về và **sẽ đi
theo khi di chuyển thư mục** — không cần tải lại. Nguồn: URL chính thức từ trang
Google AI Edge (đã xác nhận trực tiếp từ tài liệu, không đoán):
`https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task`

---

## 5. Chẩn đoán lỗi MediaPipe + đường dẫn Unicode (đã xác định RÕ NGUYÊN NHÂN GỐC bằng test thật)

### Triệu chứng ban đầu

Gọi `FaceLandmarker.create_from_options(...)` từ trong project (đường dẫn
`D:\ĐH CNTT\Học kì 3\PythonProject\ChuyenDeTN`) → **crash cứng** (không phải
exception Python bắt được):

```
F0000 ... get_runfiles_dir_helper.cc:192] Check failed:
os_helper->IsDirectoryAccessible(srcdir) srcdir "...H CNTT\H?c k... 3\PythonProject"
is not accessible!
*** Check failure stack trace: ***
```

### Đã loại trừ (test và xác nhận KHÔNG phải nguyên nhân)

- Không phải do vị trí file `python.exe` (interpreter) — test với interpreter ở
  đường dẫn ASCII thuần vẫn crash nếu CWD lúc gọi hàm là đường dẫn có dấu.
- Không phải do vị trí file script `.py` (`sys.argv[0]`) — test script đặt ở
  đường dẫn ASCII vẫn crash nếu CWD là đường dẫn có dấu.
- Không phải do biến môi trường `RUNFILES_DIR` — set biến này không thay đổi
  kết quả.
- Không phải do `VIRTUAL_ENV`/`PATH` — unset các biến này không thay đổi kết quả.
  (Ban đầu tưởng do `VIRTUAL_ENV=D:\ĐH CNTT\...\PythonProject\.venv` bị auto-set
  từ shell profile của người dùng, nhưng đã unset và vẫn crash → không phải
  nguyên nhân chính, chỉ là một yếu tố gây nhiễu lúc điều tra.)

### Nguyên nhân gốc THẬT SỰ (xác nhận bằng test cô lập rõ ràng)

**`os.getcwd()` (thư mục làm việc hiện tại của tiến trình) tại đúng thời điểm gọi
`FaceLandmarker.create_from_options()` phải là đường dẫn thuần ASCII.** Đã test:
in `os.getcwd()` ngay trước dòng gọi hàm, khi nó là đường dẫn ASCII
(`C:\Users\Acer\AppData\Local\Temp\...\scratchpad`) thì **tạo thành công** (chỉ có
vài dòng warning bình thường của TensorFlow Lite, không crash).

**Nguyên nhân phụ (phát hiện sau khi fix CWD):** đường dẫn tuyệt đối của chính
**file model `.task`** (tham số `model_asset_path`) cũng KHÔNG được chứa ký tự có
dấu — nếu không sẽ nhận `FileNotFoundError: Unable to open file at D:\ĐH
CNTT\...\face_landmarker.task` (lỗi Python bắt được bình thường, không crash cứng
nữa). Nghi vấn kỹ thuật: mã hoá ANSI/codepage hệ thống (cp1252 trên máy này)
không biểu diễn được các ký tự "Đ", "ọ", "ì"... nên lớp ctypes bên trong
MediaPipe (marshalling path sang C) hỏng khi gặp các ký tự này.

### Giải pháp đã chọn: **đổi toàn bộ đường dẫn project sang ASCII** (`D:\ChuyenDeTN`)

Đã cân nhắc 2 phương án, người dùng chọn phương án đổi path thay vì vá code:

1. ~~Vá code: `os.chdir(tempfile.gettempdir())` tạm thời trước khi khởi tạo
   `FaceLandmarker` + cache riêng file `.task` ở thư mục ASCII ngoài project~~ —
   **đã test một phần thành công** (chdir fix được lỗi crash CWD; sau đó thêm
   cache model ASCII để fix nốt FileNotFoundError — bước test kết hợp đầy đủ
   cuối cùng **chưa kịp chạy xong vì bị dừng lại** để chuyển hướng, nhưng về mặt
   logic chắc chắn sẽ hoạt động vì từng phần đã kiểm chứng riêng lẻ).
2. **✅ ĐÃ CHỌN: đổi đường dẫn project sang ASCII** `D:\ChuyenDeTN` — triệt để hơn,
   không cần patch/workaround gì trong code, mọi thứ chạy tự nhiên.

**Lưu ý cho tương lai:** nếu vì lý do nào đó phải quay lại làm việc dưới một
đường dẫn có dấu tiếng Việt, phương án workaround ở trên (chdir tạm thời + cache
model ASCII) là hướng đã kiểm chứng có cơ sở kỹ thuật vững, có thể áp dụng lại.

### Sự cố khi thực hiện di chuyển (CHƯA XONG — người dùng tự làm)

Lệnh `mv` trong Bash tool bị lỗi **`Device or resource busy`** — do chính phiên
Claude Code (CWD của tiến trình) đang giữ handle vào thư mục
`ĐH CNTT\Học kì 3\PythonProject\ChuyenDeTN`, Windows không cho đổi tên/di chuyển
thư mục đang được tiến trình khác sử dụng làm CWD. Đã xác nhận **project không hề
bị hư hại** (`git status` sạch như trước, mọi file còn nguyên) sau lần thử thất
bại này. → Người dùng tự đóng Claude Code/PyCharm và di chuyển thủ công bằng File
Explorer.

---

## 6. File đã tạo / xoá trong phiên này

| File/thư mục | Trạng thái | Ghi chú |
|---|---|---|
| `prototype/models/face_landmarker.task` | **Đã tạo**, giữ lại | Model MediaPipe, ~3.6MB, sẽ đi theo khi move |
| `.venv/` (ở vị trí project cũ) | **Đã xoá** | Cần tạo lại ở `D:\ChuyenDeTN` sau khi move (xem mục 4) |
| `prototype/tiny_diag_test.py` | **Đã tạo rồi xoá** | File chẩn đoán tạm, không còn tồn tại |
| `CLAUDE_PROGRESS.md` (file này) | **Đã tạo, đang cập nhật liên tục** | Checkpoint tiến độ |
| `.venv/` (ở `D:\ChuyenDeTN`) | **Đã tạo lại** | opencv-python 5.0.0, mediapipe 0.10.35, numpy 2.5.1 — đúng bản đã xác nhận |
| `prototype/tryon_demo.py` | **Đã viết + tự test xong** | Script chính Giai đoạn 2, xem mục 9 |

Không có file nào trong app Django (`accounts`, `products`, `cart`, `wallet`,
`wishlist`, `core`) bị sửa. App `tryon` mới **chưa được tạo** (thuộc Giai đoạn 5).

---

## 7. CHÍNH XÁC các bước tiếp theo sau khi mở lại tại `D:\ChuyenDeTN`

1. [x] Xác nhận project đã ở `D:\ChuyenDeTN`, `git status`/`git log` bình thường.
2. [x] Tạo lại venv + cài package theo lệnh ở mục 4 (dùng `py -m venv .venv` vì
   lệnh `python` trần bị Windows App Execution Alias chặn trên máy này — dùng
   `py` launcher thay thế).
3. [x] Test nhanh xác nhận `FaceLandmarker.create_from_options(...)` chạy được
   **không cần workaround** — ĐÚNG như dự đoán: chỉ có warning TFLite/XNNPACK
   bình thường, không crash. Xác nhận dứt điểm giả thuyết ở mục 5.
4. [x] Đã viết `prototype/tryon_demo.py` — 4 class tách biệt đúng kế hoạch:
   `LightNormalizer` (CLAHE trên kênh L/LAB), `FaceMeshDetector` (bọc
   `FaceLandmarker` Tasks API, chế độ `RunningMode.VIDEO` để tự bám vết),
   `GlassesOverlay` (kính demo tự vẽ bằng code — 2 elip + gọng, kênh alpha,
   đối xứng qua tâm để đơn giản hoá warp/rotate), `FPSMeter` (rolling average).
   Có cờ `--max-seconds`/`--max-frames` để tự thoát ngoài phím 'q'.
   Head pose ở giai đoạn này CHỈ có góc nghiêng (roll) suy từ 2 khoé mắt ngoài
   (landmark 33 & 263) — CHƯA tính yaw/pitch đầy đủ, việc đó để dành cho Giai
   đoạn 4 (xử lý nghiêng mặt 3/4).
5. [x] Đã tự chạy qua PowerShell với `--max-seconds 15` — **số liệu đo thật**:
   424 khung hình / 15.73 giây → **FPS trung bình 26.96**, ms/frame hiển thị
   trực tiếp trên video. Tỉ lệ phát hiện mặt 78.3% (332/424 khung hình).
   Không có exception, không crash, thoát sạch (giải phóng webcam + cửa sổ).
6. [ ] **Cần người dùng tự chạy để xem trực quan** cửa sổ OpenCV thật (Claude
   không nhìn được màn hình người dùng, chỉ đo được số liệu qua console):
   ```powershell
   .\.venv\Scripts\python.exe prototype\tryon_demo.py
   ```
   Nhấn `q` để thoát. Người dùng cần xác nhận: kính có bám đúng vị trí mắt
   không, có xoay theo góc nghiêng đầu hợp lý không, chữ FPS có hiển thị rõ
   không.
7. [ ] **ĐANG DỪNG** theo đúng quy trình — chờ người dùng xem trực quan +
   duyệt kết quả Giai đoạn 2 trước khi sang Giai đoạn 3 (tối ưu độ trễ — Bài
   toán A). Xem mục 9 để biết chi tiết đầy đủ về những gì ĐÃ làm trong phiên
   này nếu cần tiếp tục ở phiên mới.

### Việc KHÔNG được quên khi tới Giai đoạn 5 (tích hợp Django)

- Cập nhật `requirements.txt` với `opencv-python`, `mediapipe` (chưa làm, cố ý
  hoãn tới giai đoạn tích hợp theo đúng tài liệu gốc).
- Tạo `.gitignore` mới (hiện chưa có file này trong repo).
- Tạo app Django mới `tryon`, model `GlassesOverlay` (OneToOne → `Product`).
- Thêm `channels` vào `INSTALLED_APPS`, cấu hình ASGI + `InMemoryChannelLayer`.
- Không dùng Bootstrap — UI thuần CSS/vanilla JS theo `static/css/style.css`.

---

## 8. Bối cảnh môi trường máy (để tránh test nhầm lại lần nữa)

- Máy Windows, PowerShell là shell chính, Bash tool chạy qua Git Bash (MSYS2).
- Có sẵn 1 venv KHÁC (không liên quan) tại `D:\ĐH CNTT\Học kì 3\PythonProject\.venv`
  — chứa jupyter/pandas/graphify, dùng cho việc khác, không phải venv Django.
  (Thư mục `PythonProject` này giờ không còn là cha của project nữa sau khi
  move, nên không còn liên quan trực tiếp — chỉ ghi chú để tránh nhầm lẫn nếu
  còn thấy nhắc tới trong lịch sử hội thoại cũ.)
- Codepage ANSI mặc định của máy là **cp1252** (không phải cp1258 tiếng Việt) —
  đây là lý do sâu xa khiến các ký tự có dấu gây lỗi encode ở nhiều lớp khác nhau
  (không chỉ riêng MediaPipe — `pip --version` cũng từng lỗi `UnicodeEncodeError`
  tương tự khi path chứa ký tự có dấu).
- Lệnh `python` trần **không hoạt động** trong Bash tool lẫn PowerShell — bị
  Windows App Execution Alias chặn (`Python was not found; run without
  arguments to install from the Microsoft Store...`). Phải dùng **`py`**
  (Python launcher chuẩn của Windows, trỏ đúng Python 3.13.14) để tạo venv.
  Sau khi venv đã tồn tại, gọi thẳng `.\.venv\Scripts\python.exe` thì không
  gặp vấn đề này nữa.

---

## 9. NHẬT KÝ PHIÊN LÀM VIỆC — hoàn thành GIAI ĐOẠN 2 (sau khi move sang `D:\ChuyenDeTN`)

Phiên này bắt đầu ngay sau khi người dùng tự di chuyển project bằng File
Explorer (mục 5 đã dự đoán đúng). Đã làm đúng theo thứ tự mục 7 phiên trước,
không khảo sát lại từ đầu.

### Đã làm

1. Xác nhận `git status`/`git log` khớp với mục 6 (không mất gì sau khi move).
2. Tạo venv bằng `py -m venv .venv` (lệnh `python` trần bị chặn — xem mục 8),
   cài `requirements.txt` + `opencv-python` + `mediapipe`. Bản cài được: **y
   hệt** bản đã ghi nhận trước khi xoá venv cũ (`opencv-python` 5.0.0,
   `mediapipe` 0.10.35, `numpy` 2.5.1) — không có xung đột dependency.
3. Viết script test nhỏ, tự chạy, **xác nhận dứt điểm** giả thuyết ở mục 5:
   với toàn bộ path đã ASCII, `FaceLandmarker.create_from_options(...)` khởi
   tạo thành công ngay lần đầu, không cần bất kỳ workaround nào (không cần
   chdir, không cần cache model). Đã xoá file test tạm sau khi xong.
4. **Đã tra API thật** (không đoán) bằng cách introspect trực tiếp module
   `mediapipe.tasks.python.vision` trước khi code — xác nhận `RunningMode`
   có 3 giá trị `IMAGE`/`VIDEO`/`LIVE_STREAM`, chữ ký đầy đủ của
   `FaceLandmarkerOptions.__init__`. Dùng `RunningMode.VIDEO` +
   `detect_for_video(mp_image, timestamp_ms)` (không dùng `IMAGE` mode) để
   MediaPipe tự bám vết giữa các khung hình.
5. Viết `prototype/tryon_demo.py` hoàn chỉnh, cấu trúc 4 class:
   - `LightNormalizer`: CLAHE trên kênh L (không gian LAB), có sẵn
     `is_low_light()`/`mean_brightness()` để Giai đoạn 4 tái sử dụng cho
     cảnh báo thiếu sáng.
   - `FaceMeshDetector`: bọc `FaceLandmarker` Tasks API, dùng landmark 33
     (khoé mắt ngoài bên phải người dùng, anatomical) và 263 (khoé mắt
     ngoài bên trái) để suy ra vị trí/kích thước/góc nghiêng (roll) — CHƯA
     tính yaw/pitch đầy đủ bằng `output_facial_transformation_matrixes`
     hay `solvePnP` (việc đó dành cho Giai đoạn 4, quyết định có chủ đích
     để giữ Giai đoạn 2 đơn giản, đúng tinh thần "giải pháp đơn giản hơn
     giải pháp phức tạp").
   - `GlassesOverlay`: vì project **chưa có PNG kính thật nào** (441 ảnh
     hiện có đều là `.jpg` chụp thật, không nền trong suốt), tự vẽ kính
     demo bằng `cv2.ellipse`/`cv2.line` với kênh alpha, cố tình vẽ **đối
     xứng qua tâm** để tâm ảnh trùng đúng trung điểm 2 mắt kính, đơn giản
     hoá việc resize/rotate (không cần lưu anchor point riêng như PNG thật
     sẽ cần ở Giai đoạn 5). Dùng `cv2.getRotationMatrix2D` +
     `cv2.warpAffine` để xoay theo góc nghiêng đầu, alpha-blend thủ công
     bằng NumPy.
   - `FPSMeter`: rolling average FPS (deque 30 frame) + ms/frame, vẽ trực
     tiếp lên khung hình.
   - Cờ `--max-seconds`/`--max-frames` để tự động thoát ngoài phím `q` —
     mục đích: tự đo FPS qua console được, không phải chờ người dùng bấm
     tay mỗi lần test.
   - Xử lý lỗi: webcam không mở được (`cap.isOpened()`), file model thiếu
     (`FileNotFoundError` rõ ràng), không có khuôn mặt (bỏ qua overlay,
     hiện chữ tiếng Việt), 2 landmark trùng nhau/khoảng cách mắt ~0 (tránh
     chia cho 0). Giải phóng `cap` + `cv2.destroyAllWindows()` +
     `detector.close()` trong khối `finally`.
6. Tự chạy `--max-seconds 15` qua PowerShell (webcam thật của người dùng) —
   **số liệu đo thật, không phỏng đoán**:
   - Tổng khung hình: 424 trong 15.73 giây
   - **FPS trung bình: 26.96**
   - Tỉ lệ khung hình phát hiện được mặt: 78.3% (332/424)
   - Không có exception, không crash, thoát sạch tài nguyên.

### Việc CHƯA làm — cần ở đầu phiên tiếp theo

- **Chưa có xác nhận trực quan từ người dùng.** Claude không nhìn được màn
  hình người dùng nên không biết kính có bám đúng vị trí/góc xoay hợp lý
  trên khuôn mặt thật hay không — chỉ biết pipeline chạy không lỗi và FPS
  đo được. Việc đầu tiên khi mở lại phiên: hỏi người dùng đã tự chạy
  `prototype/tryon_demo.py` xem trực quan chưa, kết quả thế nào.
- Nếu người dùng duyệt → chuyển sang **GIAI ĐOẠN 3** (tối ưu độ trễ, đo
  bảng FPS trước/sau từng kỹ thuật — xem PROMPT gốc mục "GIAI ĐOẠN 3").
  FPS ~27 hiện tại đo trên toàn bộ pipeline CHƯA tối ưu gì cả (chưa giảm
  độ phân giải nhận diện, chưa One-Euro filter, chưa giới hạn tần suất
  detect...) — đây chính là baseline để so sánh ở Giai đoạn 3.
- Nếu người dùng phản hồi kính lệch vị trí/lệch góc xoay → nhiều khả năng
  do 2 vấn đề đã lường trước trong code (xem comment trong
  `GlassesOverlay.render_on_frame`): (a) hệ số scale `eye_distance /
  anchor_span` dùng khoảng cách khoé mắt NGOÀI (rộng hơn khoảng cách đồng
  tử thật ~20-30mm) làm xấp xỉ trực tiếp cho độ rộng kính — có thể cần
  thêm hệ số nhân điều chỉnh; (b) dấu góc xoay `-angle_deg` đã tính tay
  và kiểm chứng logic trên giấy nhưng CHƯA được xác nhận bằng mắt thật.

---

## 10. NHẬT KÝ PHIÊN LÀM VIỆC — dọn catalog + đổi tên wishlist→favorites (2026-07-31)

**Lưu ý về đường dẫn:** project hiện đang ở `D:\DoAnTN` (không phải
`D:\ChuyenDeTN` như mục 1 mô tả — người dùng đã đổi tên thư mục ở đâu đó
giữa các phiên, không ghi nhận lại chi tiết). Đường dẫn vẫn thuần ASCII nên
không ảnh hưởng gì tới chẩn đoán MediaPipe ở mục 5.

Phiên này KHÔNG đụng vào module try-on (vẫn đang dừng ở Giai đoạn 2, chờ
người dùng xác nhận trực quan — xem mục 9). Người dùng chuyển hướng sang
dọn dẹp phần catalog Django trước khi tiếp tục try-on. Đã làm:

1. **Asset kính nền trong suốt**: người dùng tự tách nền một ảnh kính
   (`anh_tachnen/kinh.png` — kính vuông (Square) màu đen, chụp thẳng mặt,
   đối xứng, nền trong suốt) nhưng không biết đặt ở đâu. Đây đúng loại ảnh
   mà mục 5.2/quyết định #3 đã xác định là còn thiếu cho `GlassesOverlay`
   (Giai đoạn 5 try-on — 441 ảnh sản phẩm cũ đều là `.jpg` chụp thật, không
   có ảnh nền trong suốt nào). Đã di chuyển sang
   **`media/tryon/glasses/kinh.png`** — nằm trong `media/` (giống quy ước
   `ProductImage.image` dùng `upload_to="products/gallery/"`) để khi tạo
   model `GlassesOverlay` ở Giai đoạn 5, chỉ cần trỏ `upload_to="tryon/glasses/"`
   là dùng lại được file này làm dữ liệu mẫu, không cần app `tryon` tồn tại
   trước. Đã xoá thư mục `anh_tachnen/` rỗng sau khi di chuyển.

2. **Đổi tên app `wishlist` → `favorites`** (theo yêu cầu người dùng). App
   này trước giờ chỉ có model + admin, CHƯA có `urls.py`/view thật, chưa
   từng include vào `core/urls.py` (dòng include bị comment sẵn) — nên đổi
   tên an toàn, không ảnh hưởng chức năng đang chạy. Đã làm:
   - `manage.py migrate wishlist zero` để xoá sạch bảng cũ trước khi đổi
     tên (bảng rỗng, không có dữ liệu thật vì chưa có view nào ghi vào).
   - Đổi thư mục `wishlist/` → `favorites/`, model `Wishlist` → `Favorite`,
     `related_name` trên `User` đổi `wishlist` → `favorites`, trên `Product`
     đổi `wishlisted_by` → `favorited_by`.
   - Cập nhật `apps.py` (`WishlistConfig` → `FavoritesConfig`, `name =
     "favorites"`), `admin.py` (`FavoriteAdmin`), `core/settings.py`
     (`INSTALLED_APPS`), `accounts/signals.py` (import + gọi
     `Favorite.objects.get_or_create`), comment trong `cart/models.py`,
     `accounts/views.py`, `accounts/apps.py`, `core/urls.py` (dòng include
     đang comment đổi thành `favorites.urls` tại prefix `yeu-thich/`).
   - Xoá migration cũ, chạy `makemigrations favorites` + `migrate` tạo lại
     bảng mới từ đầu. Đã chạy `manage.py check` — sạch, 0 lỗi.
   - Text UI "Yêu thích"/"Sản phẩm yêu thích" trong `templates/base.html`
     vốn đã là tiếng Việt đúng nghĩa "favorites" nên KHÔNG cần sửa gì thêm.

3. **Dọn catalog sản phẩm**: người dùng yêu cầu chỉ giữ lại 3 sản phẩm dáng
   Square, xoá hết phần còn lại, xoá luôn category thừa. Đã hỏi lại phạm vi
   xoá category (xoá hẳn tính năng category khỏi code, hay chỉ xoá dữ liệu
   thừa) — người dùng chọn **chỉ xoá dữ liệu thừa**, giữ nguyên toàn bộ
   model/view/template/JS liên quan tới category. Đã thực hiện qua Django
   ORM (không sửa tay migration):
   - Chọn giữ lại 3 sản phẩm trong category "Vuông (Square)" (trước có 7):
     `Incantation` (id=37), `Mythic` (id=66), `Impossible` (id=68) — chọn 3
     tên khác nhau (không trùng biến thể màu) để catalog demo có sự đa dạng.
   - `Product.objects.exclude(pk__in=[37, 66, 68]).delete()` → xoá 68 sản
     phẩm, cascade xoá theo 344 `ProductImage` (ảnh gallery) + 3 `CartItem`
     đang trỏ tới các sản phẩm đó. File ảnh vật lý trong `media/products/`
     KHÔNG bị xoá khỏi ổ đĩa (chỉ xoá bản ghi DB) — cân nhắc dọn tay sau nếu
     cần tiết kiệm dung lượng, không bắt buộc.
   - `Category.objects.exclude(pk=10).delete()` → xoá 10 category thừa, chỉ
     còn lại "Vuông (Square)" (id=10).
   - Dữ liệu gốc đầy đủ (71 sản phẩm/11 category) vẫn còn nguyên trong
     `seed_products.sql` ở gốc repo — có thể re-seed lại nếu cần khôi phục.
   - Đã xác nhận lại bằng cách chạy `runserver` cục bộ + `curl`: trang chủ
     `/` trả 200, đúng 3 `product-card` + 1 `category-card`; trang chi tiết
     `/san-pham/incantation-black/`, `/san-pham/mythic-gold-blue-light-lens/`,
     `/san-pham/impossible-tokyo-tort/` đều trả 200.

### Việc CHƯA làm / lưu ý cho phiên sau

- Try-on module vẫn đang chờ người dùng xác nhận trực quan Giai đoạn 2 (mục
  9) — chưa sang Giai đoạn 3.
- `media/tryon/glasses/kinh.png` mới chỉ là asset nằm sẵn ở đúng chỗ, CHƯA
  có model `GlassesOverlay`/app `tryon` nào tham chiếu tới nó (việc đó vẫn
  thuộc Giai đoạn 5 theo kế hoạch gốc, chưa được yêu cầu làm ngay).
- File media ảnh của 68 sản phẩm đã xoá vẫn còn nằm rải rác trong
  `media/products/` và `media/products/gallery/` (không xoá đĩa), chỉ dọn
  nếu người dùng yêu cầu.

11. PROMPT CHO PHIÊN TIẾP THEO — Ghép PNG THẬT + Giai đoạn 3 (độ trễ) + Giai đoạn 4 (che khuất/thiếu sáng/khẩu trang)

Đây là chỉ dẫn cho phiên Claude Code kế tiếp. Đọc kỹ mục 7, 9 ở trên trước (KHÔNG khảo sát lại codebase, KHÔNG làm lại việc đã xong). Làm TỪNG GIAI ĐOẠN, dừng chờ tôi duyệt sau mỗi giai đoạn. Tự kiểm lỗi kỹ, KHÔNG đoán API (tra tài liệu / introspect như đã làm ở mục 9), gặp bug thì phân tích nguyên nhân gốc rồi mới sửa. Comment tiếng Việt, code dễ hiểu. Cập nhật chính file này sau mỗi bước.

Bước 0 — Xác nhận Giai đoạn 2

Hỏi tôi đã chạy prototype\tryon_demo.py xem trực quan chưa và kính bám có hợp lý không. Nếu tôi báo lệch vị trí/lệch góc → xử lý 2 khả năng đã lường trước trong comment GlassesOverlay.render_on_frame (hệ số scale theo khoé mắt ngoài; dấu góc xoay). Nếu tôi đã OK → sang Bước 1.

Bước 1 — Chuyển sang ẢNH PNG THẬT (quan trọng, cập nhật mới)

Tôi đã có ảnh PNG kính chụp chính diện, nền trong suốt, cắt sát viền. Đường dẫn: [ĐIỀN ĐƯỜNG DẪN ẢNH PNG CỦA TÔI VÀO ĐÂY].

Nâng cấp GlassesOverlay từ kính-vẽ-tạm sang ghép ảnh PNG thật (giữ nguyên interface để phần còn lại không phải sửa).
Thêm tham số hiệu chỉnh cho mỗi mẫu, KHÔNG hard-code: width_ratio (bề rộng kính so với khoảng cách hai mắt) và vertical_offset (độ lệch dọc so với trung điểm hai mắt). Cho tôi cách chỉnh nhanh 2 số này để căn 1 lần dùng mãi.
Tôn trọng kênh alpha thật của PNG (không để viền); xử lý khi PNG thiếu/hỏng.

DỪNG — cho tôi xem kính PNG bám mặt trực quan, chỉnh hệ số nếu cần.

Bước 2 — GIAI ĐOẠN 3: Khắc phục độ trễ (Bài toán A của giảng viên)

Baseline hiện tại = 26.96 FPS (mục 9), pipeline chưa tối ưu gì. Áp từng kỹ thuật và đo FPS trước/sau từng cái, lập bảng so sánh (số liệu cho báo cáo, phải đo thật):

Thu nhỏ ảnh đưa vào nhận diện (rộng ~320–480px) nhưng vẽ kính lên ảnh gốc.
Giảm tần suất detect (~15 FPS) và nội suy / tái dùng landmark giữa các lần.
One-Euro filter làm mượt (tâm, bề rộng, góc) — chống rung, giảm cảm giác trễ.
Cache ảnh PNG đã giải mã một lần (không đọc lại file mỗi khung).
Chỉ xử lý ROI quanh mắt, bỏ qua khi không có mặt.

DỪNG — báo cáo bảng FPS trước/sau.

Bước 3 — GIAI ĐOẠN 4: Che khuất, thiếu sáng, khẩu trang (Bài toán B)

KHÔNG train lại mô hình, KHÔNG augmentation. Dùng MediaPipe pre-trained + xuống cấp duyên dáng.

Thiếu sáng: kích hoạt LightNormalizer (CLAHE, đã có sẵn) tự động khi is_low_light(); so sánh tỉ lệ phát hiện mặt trước/sau khi bật chuẩn hóa.
Khẩu trang: kiểm chứng vùng mắt + sống mũi không bị che nên vẫn chạy; ghi nhận kết quả thực nghiệm (điểm mạnh cho báo cáo).
Che khuất / mất tín hiệu: gating theo độ tin cậy; nếu thấp hoặc mất mặt N khung liên tiếp → ẩn kính + thông báo tiếng Việt, không vẽ sai.
Nghiêng mặt (yaw): tính yaw đầy đủ (dùng output_facial_transformation_matrixes hoặc solvePnP — đã ghi chú để dành ở mục 9). Trong vùng an toàn (~dưới 35°) hiển thị bình thường; vượt ngưỡng → mờ dần rồi ẩn kính + gợi ý "Vui lòng nhìn thẳng hơn vào camera". (Kỹ thuật một-ảnh-2D không xử lý được góc lớn — chỉ cần xuống cấp an toàn.)
Viết script kiểm thử để tôi tự quay từng tình huống và ghi lại tỉ lệ hoạt động ổn định — dùng cho phần "ghi nhận các trường hợp giới hạn" trong báo cáo.

DỪNG — báo cáo kết quả kiểm thử từng ca.

Sau đó

Chỉ khi 3 bước trên xong và tôi duyệt mới sang Giai đoạn 5 (tích hợp Django) theo mục 7: tạo app tryon, model GlassesOverlay OneToOne → Product, cấu hình channels/ASGI, UI thuần CSS/vanilla JS (KHÔNG Bootstrap), cập nhật requirements.txt + .gitignore.

---

## 12. NHẬT KÝ PHIÊN LÀM VIỆC — Bước 0 + Bước 1 của mục 11 (ghép PNG thật)

Người dùng xác nhận Bước 0 (Giai đoạn 2) ổn ("mọi thứ khá ổn") mà không báo lệch vị trí/góc cụ thể nào → không cần vá `GlassesOverlay` cũ, đi thẳng Bước 1.

### Đã làm — nâng cấp `prototype/tryon_demo.py`, class `GlassesOverlay`

- **Ghép ảnh PNG thật** `media/tryon/glasses/kinh.png` (1200×1200px, RGBA, đã xác nhận bằng PIL trước khi code: bbox nội dung (86,450)-(1121,816), tâm ~(603,632)) thay cho kính vẽ tay. Interface `render_on_frame(frame_bgr, pt_a, pt_b)` giữ nguyên — phần còn lại của pipeline không phải sửa.
- **Tâm neo (anchor) tự động** = tâm bbox vùng alpha>0 của ảnh (không hard-code như bản demo cũ dùng tâm canvas) — tổng quát hoá, dùng được với bất kỳ PNG thật nào kể cả khi nội dung không nằm chính giữa canvas.
- **2 tham số hiệu chỉnh** truyền qua CLI, KHÔNG hard-code:
  - `--width-ratio` (mặc định 1.6): bề rộng kính hiển thị = `eye_distance * width_ratio`.
  - `--vertical-offset` (mặc định 0.0): lệch dọc tâm kính so với trung điểm 2 mắt, tính theo TỶ LỆ của `eye_distance` (không phải pixel cố định) để giữ đúng tỷ lệ khi mặt gần/xa camera.
- **Cách chỉnh nhanh 1 lần dùng mãi (cải tiến thêm ngoài yêu cầu gốc)**: chỉnh trực tiếp bằng phím khi đang xem webcam, không cần sửa code/khởi động lại — `+`/`-` chỉnh `width_ratio` (bước 0.05), `[`/`]` chỉnh `vertical_offset` (bước 0.01), `s` in ra console dòng lệnh đầy đủ để dán lại làm mặc định mới. Giá trị hiện tại luôn hiện ở góc dưới-trái video, và được tự in ra khi thoát chương trình (kể cả quên bấm `s`).
- **Sửa lỗi viền (fringing/halo)** — vấn đề kinh điển khi resize/xoay ảnh RGBA có biên chống răng cưa: nếu không xử lý, nội suy bilinear sẽ trộn màu RGB của vùng trong suốt (thường sót màu đen/trắng từ bước tách nền) vào vùng đục kề bên, tạo viền màu lạ quanh kính sau khi blend. Đã áp dụng kỹ thuật **premultiplied alpha** chuẩn của đồ hoạ máy tính: nhân RGB với alpha trước khi resize/xoay, dùng công thức blend "over" tương ứng khi ghép — đã test bằng ảnh nền màu da giả lập, xác nhận không còn viền (xem ảnh test, đã xoá sau khi kiểm tra).
- **Xử lý PNG thiếu/hỏng**: nếu `--glasses-png` không tồn tại, không đọc được, hoặc không có kênh alpha → in cảnh báo cụ thể ra console và tự động dùng lại kính vẽ demo (giữ code cũ `_draw_demo_glasses` làm phương án dự phòng, không xoá).

### Đã tự kiểm tra (không cần webcam)

- `py_compile` sạch, không lỗi cú pháp.
- Test độc lập `GlassesOverlay` (không webcam): nạp PNG thật OK, ghép + xoay theo góc nghiêng giả lập OK, trường hợp PNG thiếu tự chuyển fallback demo OK, trường hợp 2 landmark trùng nhau (chia cho 0) không crash.
- Render thử 1 khung hình giả lập ra file ảnh, xác nhận bằng mắt: kính nằm đúng giữa 2 điểm neo, không có viền màu lạ quanh biên.

### Việc CHƯA làm — cần người dùng tự test bằng webcam thật trước khi sang Bước 2

Theo đúng mục 11, DỪNG ở đây chờ người dùng xem trực quan PNG thật bám mặt (Claude không xem được webcam):

```powershell
.\.venv\Scripts\python.exe prototype\tryon_demo.py
```

Chỉnh `+`/`-`/`[`/`]` trực tiếp khi đang xem đến khi kính vừa mắt, bấm `s` (hoặc cứ `q` thoát — giá trị cuối tự in ra console) để lấy 2 số `width_ratio`/`vertical_offset` cuối cùng. Báo lại 2 số đó (hoặc chỉ cần nói "ổn rồi") để phiên sau ghi làm mặc định cố định và chuyển sang **Bước 2 — Giai đoạn 3 (tối ưu độ trễ)**.
---

## 13. PROMPT PHIÊN TIẾP THEO — Tự động căn kính (BỎ chỉnh tay) + Multi-view góc nghiêng (thêm ảnh 3/4)

> Người dùng đổi hướng ở Bước 1: KHÔNG muốn chỉnh tay `width_ratio`/`vertical_offset`
> nữa — muốn kính **tự khớp mắt/khuôn mặt** khi chọn. Đồng thời thêm **ảnh 3/4** để
> khi quay đầu ngang thì đổi sang ảnh đó. Đọc kỹ mục 9, 11, 12 trước. Làm TỪNG BƯỚC,
> **dừng chờ người dùng test webcam** sau mỗi bước. Tự kiểm lỗi, KHÔNG đoán API, phân
> tích nguyên nhân gốc. Comment tiếng Việt. **Giữ code cũ làm fallback, KHÔNG xoá.**
> Cập nhật file này sau mỗi bước.

### Bước A — Tự động căn kính bằng 2 điểm neo (thay cho chỉnh tay)

Vấn đề của bản hiện tại: chỉ dùng 1 điểm neo (tâm alpha) + 2 số chỉnh tay. Thay bằng
**2 điểm neo = tâm hai tròng kính**, ánh xạ sang tâm hai mắt → tự ra co giãn + xoay +
vị trí, KHÔNG cần `width_ratio`/`vertical_offset` thủ công.

1. **Tự tìm tâm 2 tròng trong ảnh PNG**: trong vùng silhouette (alpha>0), tìm **hai
   vùng "lỗ tròng"** (vùng trong suốt hoặc đục nhạt được gọng bao quanh) lớn nhất;
   lấy **centroid** mỗi vùng; phân trái/phải theo tọa độ x. Lưu 2 điểm này là anchor
   của ảnh (tính 1 lần khi nạp ảnh, cache lại).
2. **Điểm mắt trên khuôn mặt**: dùng **tâm 2 mắt** từ MediaPipe (trung bình các
   landmark quanh mỗi mắt cho ổn định, đừng chỉ lấy 1 điểm).
3. **Ghép bằng phép biến đổi tương tự (similarity)**: từ 2 cặp điểm (tròng↔mắt) tính
   scale + góc + tịnh tiến, áp vào ảnh rồi alpha-blend. Không còn số chỉnh tay.
4. **Fallback (bắt buộc giữ)**: nếu KHÔNG tìm được 2 tròng đáng tin (gọng quá mảnh /
   rimless / tròng cùng màu nền) → in cảnh báo và **quay lại phương pháp `width_ratio`
   cũ** (giữ nguyên code phím `+/-` làm dự phòng). Không được xoá đường cũ.
5. **Tự kiểm tra**: render vài khung giả lập với ảnh kính thật, xác nhận bằng mắt tâm
   2 tròng nằm đúng vào 2 mắt, không lệch, không viền.

**DỪNG — người dùng test webcam: chọn kính có tự khớp mắt không, còn phải bấm phím
chỉnh nữa không.**

### Bước B — Multi-view: thêm ảnh 3/4, tự đổi theo góc quay đầu (yaw)

Kéo phần tính **yaw** (vốn để dành Giai đoạn 4) lên đây vì cần nó để đổi ảnh.

1. **Tính yaw** từ `output_facial_transformation_matrixes` của FaceLandmarker (hoặc
   `solvePnP`); làm mượt bằng One-Euro để không rung khi chuyển ảnh.
2. **Nạp 2 ảnh cho mỗi mẫu**: ảnh **chính diện** và ảnh **3/4**. Mỗi ảnh tự tính 2
   điểm neo tròng như Bước A (ảnh 3/4 vẫn thấy 2 tròng, foreshortened).
3. **Chọn ảnh theo yaw**:
   - `|yaw|` nhỏ (≈ dưới 18°) → dùng ảnh **chính diện**.
   - trung bình (≈ 18–40°) → dùng ảnh **3/4**.
   - lớn (≈ trên 40°) → **mờ dần rồi ẩn** + gợi ý "Vui lòng nhìn thẳng hơn vào camera".
4. **Lật gương**: ảnh 3/4 chỉ render một bên. Khi đầu quay hướng ngược lại → **lật
   ngang ảnh** (`cv2.flip(img,1)`) VÀ **hoán đổi hai điểm neo trái/phải** cho khớp.
5. **Crossfade** giữa ảnh chính diện và ảnh 3/4 quanh ranh giới góc (đổi độ mờ theo
   yaw) để không bị "nhảy" ảnh đột ngột.

**Đường dẫn ảnh** (người dùng điền/đặt):
- Chính diện: `[ĐIỀN ĐƯỜNG DẪN ẢNH CHÍNH DIỆN]`
- 3/4: `[ĐIỀN ĐƯỜNG DẪN — ví dụ media/tryon/glasses/Jasmin_01_BL__3_4.png]`

**DỪNG — người dùng test webcam: quay trái/phải xem kính có đổi sang ảnh 3/4 mượt
không, lật đúng bên không.**

### Bổ sung Bước B — Quy ước đặt tên & gộp 2 ảnh thành 1 mẫu kính

Mỗi mẫu kính = **một bộ 2 ảnh**, gộp theo **tên file**:

- Quy ước hậu tố **CỐ ĐỊNH** (không đặt lẫn lộn kiểu khác):
  - `<ten_mau>_f.png`  → ảnh **chính diện** (front)
  - `<ten_mau>_34.png` → ảnh **góc 3/4**
  - Ví dụ: `jasmin_f.png` + `jasmin_34.png` là **một mẫu** (`jasmin`);
    `aurora_f.png` + `aurora_34.png` là mẫu khác.
- Cách code gom: quét thư mục ảnh kính, **nhóm các file theo phần gốc tên** (bỏ hậu
  tố `_f`/`_34`), mỗi nhóm là một mẫu; trong nhóm phân loại ảnh theo hậu tố. Thêm mẫu
  mới = thả 2 file đúng tên vào thư mục, **KHÔNG sửa code**.
- **Chọn nhiều mẫu**: liệt kê các mẫu tìm được để người dùng chọn; khi chọn mẫu nào
  thì nạp đúng bộ 2 ảnh của mẫu đó (mỗi ảnh tự tính điểm neo tròng như Bước A), rồi
  tự đổi ảnh theo yaw như Bước B. Đổi mẫu là nạp bộ ảnh mới.
- **Xử lý thiếu ảnh (bắt buộc)**: nếu một mẫu **chỉ có ảnh `_f`** mà thiếu `_34` →
  KHÔNG crash; vẫn chạy bình thường với ảnh chính diện, khi quay ngang thì mờ/ẩn kính
  như cơ chế cũ. Nhờ vậy không bắt buộc mọi mẫu phải đủ 2 ảnh ngay từ đầu. Nếu thiếu
  ảnh `_f` thì bỏ qua mẫu đó + in cảnh báo (ảnh chính diện là tối thiểu bắt buộc).
- Ghi **quy ước hậu tố này vào tài liệu/README** để phiên sau và người dùng không đặt
  tên lệch (`-front`, `_3_4`, `.f`…) khiến không gom được cặp.

> Lưu ý cho Giai đoạn 5 (Django): khi tích hợp, "gộp theo tên file" sẽ chuyển thành
> **2 trường ảnh trong model `GlassesOverlay`** (`image_front`, `image_34`) thay cho
> quy ước tên file — sạch hơn. Ở prototype hiện tại thì gộp theo tên file là đủ và nhanh.

---

## 14. NHẬT KÝ PHIÊN LÀM VIỆC — hoàn thành BƯỚC A của mục 13 (tự động căn kính)

**Bối cảnh khi mở phiên**: người dùng đã tự chuẩn bị sẵn 2 bộ ảnh kính thật theo
đúng quy ước đặt tên của Bước B (`Jasmin 01(BL)_f.png` + `_34.png`, `Vanta 02_f.png`
+ `_34.png`) trong `media/tryon/glasses/`, và **đã xoá `kinh.png` cũ**. Hai bộ ảnh
tình cờ đại diện đúng 2 kiểu tròng kính khác nhau cần xử lý — rất hữu ích để tự
kiểm chứng thuật toán:
- `Vanta 02` — gọng kim loại mảnh, tròng **trong suốt thật** (alpha=0).
- `Jasmin 01(BL)` — gọng nhựa dày, tròng **nhuộm màu nhưng vẫn đục** (alpha=255,
  chỉ nhạt màu hơn gọng).

### Đã làm — `prototype/tryon_demo.py`, class `GlassesOverlay`

1. **`_find_lens_anchors(bgra)` (static)** — tự động tìm tâm 2 tròng kính, hỗ trợ
   cả 2 trường hợp trên:
   - **Trường hợp (a) — lỗ thật**: dùng `cv2.findContours(..., RETR_CCOMP)` để
     lấy contour phân cấp cha/con; đường viền ngoài lớn nhất = silhouette kính;
     các contour con trực tiếp của nó = lỗ thật do alpha=0 bị gọng bao kín. Lấy
     2 lỗ lớn nhất (lọc nhiễu <2% diện tích bbox), tính centroid bằng
     `cv2.moments`.
   - **Trường hợp (b) — tròng đục nhạt màu hơn gọng**: nếu không đủ 2 lỗ thật,
     chuyển sang phân ngưỡng Otsu trên độ sáng grayscale **chỉ trong vùng
     silhouette**. Xác định lớp nào là "gọng" bằng cách so lớp nào **chạm nhiều
     hơn vào vành mỏng sát viền ngoài** (`erode` rồi trừ) — vì gọng luôn CHÍNH LÀ
     đường viền ngoài, không giả định cố định "gọng tối hơn tròng" (tránh sai với
     kính gọng bạc/tròng tối). Lớp còn lại → `cv2.connectedComponentsWithStats`,
     lấy 2 vùng lớn nhất.
   - Trả về `None` nếu không đủ tin cậy (kích hoạt fallback ở bước 3).
2. **`_similarity_matrix_2pt(src1, src2, dst1, dst2)` (static)** — tính ma trận
   affine 2×3 (xoay đều + tỷ lệ đều + tịnh tiến, KHÔNG lật gương) duy nhất thoả 2
   cặp điểm, bằng công thức số phức `a = (dst2-dst1)/(src2-src1)`.
3. **`render_on_frame_auto(frame, eye_a, eye_b)`** — đường chính mới:
   - Nếu ảnh không có `_lens_left`/`_lens_right` (từ bước 1) → tự gọi lại
     `render_on_frame` cũ (chế độ dự phòng 1-điểm-neo + `width_ratio`, **giữ
     nguyên, không xoá**).
   - Nếu có 2 tâm tròng: **tự chọn chiều ghép** (tròng-trái↔eye_a hay
     tròng-trái↔eye_b) theo chiều nào cho **góc xoay kết quả nhỏ nhất** — vì kính
     đeo đúng luôn gần thẳng hàng với 2 mắt (lệch nhẹ theo độ nghiêng đầu thật,
     không bao giờ gần 180°). Cách này **tự đúng bất kể quy ước trái/phải của ảnh
     sản phẩm có khớp chiều với landmark khuôn mặt đã lật gương hay không** —
     không cần giả định cứng (đã cân nhắc kỹ vì not chắc chắn 100% quy ước
     `cv2.flip` + landmark 33/263, xem docstring trong code).
   - Warp trực tiếp `warpAffine` cả ảnh premultiplied lên kích thước khung hình
     rồi alpha-blend — không cần bước resize/rotate riêng như code cũ.
4. **`_set_image`** thêm tham số `detect_lens_anchors` (mặc định `True`); kính
   demo vẽ tay (`_draw_demo_glasses`, dùng khi PNG lỗi/thiếu) gọi với `False` để
   luôn đi thẳng chế độ dự phòng — không chạy dò tâm tròng vô nghĩa trên ảnh vẽ
   tay.
5. **`draw_calibration_hint`** đổi hiển thị theo chế độ thực tế: chữ xanh lá "Chế
   độ: TỰ ĐỘNG..." khi có tâm tròng, chữ vàng "Chế độ DỰ PHÒNG..." kèm 2 số
   `width_ratio`/`vertical_offset` khi không có (chỉ khi đó phím `+/-/[/]` mới có
   tác dụng).
6. **`main()`**: thêm `_default_glasses_png()` — tự quét `media/tryon/glasses/`
   tìm file `*_f.png` đầu tiên (sắp theo tên) làm mặc định thay cho `kinh.png` đã
   xoá (mặc định hiện ra là `Jasmin 01(BL)_f.png`); đổi lời gọi render sang
   `render_on_frame_auto`; cập nhật tên cửa sổ + thông báo kết quả cuối theo đúng
   chế độ đang chạy.

### Đã tự kiểm tra kỹ (không cần webcam, theo đúng thói quen mục 12)

- `py_compile` sạch.
- **Test tìm tâm tròng trên cả 4 ảnh thật** (`_f`/`_34` của cả 2 mẫu): vẽ tâm phát
  hiện được lên ảnh, xem trực quan — cả 4 ảnh đều đúng tâm tròng, kể cả ảnh 3/4
  (góc nghiêng, tròng bị foreshortened).
- **Test render trên khung hình giả lập** (nền màu da giả, 2 điểm mắt giả):
  - Kính thẳng (mắt ngang hàng): kính hiện đúng giữa, không lệch.
  - **Đổi chỗ eye_a/eye_b** (mô phỏng tình huống không chắc chiều trái/phải) →
    ra kết quả **giống hệt** bản không đổi chỗ — xác nhận cơ chế tự chọn góc xoay
    nhỏ nhất hoạt động đúng, không bị lật ngược 180°.
  - Mắt nghiêng 2 chiều ngược nhau (giả lập nghiêng đầu trái/phải) → kính xoay
    đúng theo, không lật ngược, cả với ảnh Jasmin (case Otsu) lẫn Vanta (case lỗ
    thật).
  - Fallback (gọi `GlassesOverlay(None)` → kính vẽ demo) vẫn hoạt động y hệt
    logic cũ, không bị ảnh hưởng bởi thay đổi.
- `--help` chạy sạch, xác nhận mặc định `--glasses-png` tự trỏ đúng
  `Jasmin 01(BL)_f.png`.

### Việc CHƯA làm — cần người dùng tự test webcam thật trước khi sang Bước B

Theo đúng mục 13, DỪNG ở đây chờ xác nhận trực quan (Claude không xem được
webcam):

```powershell
.\.venv\Scripts\python.exe prototype\tryon_demo.py
.\.venv\Scripts\python.exe prototype\tryon_demo.py --glasses-png "media\tryon\glasses\Vanta 02_f.png"
```

Cần xác nhận: kính có tự khớp đúng vào mắt không (không cần bấm phím chỉnh gì),
góc xoay có hợp lý khi nghiêng đầu nhẹ không, HUD có hiện đúng "Chế độ: TỰ ĐỘNG"
màu xanh lá không. Nếu ổn → chuyển sang **Bước B (mục 13)**: tính yaw, thêm đổi
ảnh chính diện/3-4 theo góc quay đầu, gộp theo tên file, chọn mẫu kính. Nếu kính
lệch/xoay sai → báo cụ thể lệch kiểu gì (lệch ngang/dọc, xoay sai chiều, sai tỷ
lệ) để chẩn đoán đúng nguyên nhân gốc trước khi sửa.

---

## 15. NHẬT KÝ PHIÊN LÀM VIỆC — hoàn thành BƯỚC B của mục 13 (đổi ảnh 3/4 theo yaw)

Người dùng xác nhận Bước A "kính định vị khá tốt" → làm thẳng Bước B (đổi ảnh
chính diện/3-4 theo góc quay đầu) + phần "Bổ sung Bước B" (quy ước tên file, gộp
mẫu, chọn mẫu) trong cùng phiên vì cả 2 phần gắn chặt với nhau.

### Đã làm — `prototype/tryon_demo.py`

1. **Tính yaw bằng `cv2.solvePnP`** (method mới `FaceMeshDetector.estimate_yaw_deg`)
   — dùng mô hình mặt 3D chuẩn 6 điểm (đỉnh mũi, cằm, 2 khoé mắt ngoài, 2 khoé
   miệng — landmark 1/152/33/263/61/291, là các chỉ số phổ biến trong nhiều dự
   án head-pose-estimation-từ-MediaPipe công khai) + camera matrix xấp xỉ
   (focal = chiều rộng khung hình). **Đã tự kiểm chứng công thức bằng test hình
   học tổng hợp độc lập** (dựng điểm 3D xoay góc biết trước, chiếu xuống 2D bằng
   `cv2.projectPoints`, chạy `solvePnP` ngược lại, so khớp góc thu được với góc
   đã xoay — khớp chính xác từ -40° đến +40°) — **KHÔNG đoán công thức**, nhưng
   **KHÔNG kiểm chứng được trên khuôn mặt thật** vì môi trường này không có
   webcam. Không dùng `output_facial_transformation_matrixes` (tránh phụ thuộc
   một API chưa rõ quy ước trục nội bộ).
2. **`OneEuroFilter`** (class mới, thuật toán chuẩn Casiez/Roussel/Vogel 2012) —
   làm mượt tín hiệu yaw theo thời gian thực, chống rung khi đầu gần như đứng
   yên nhưng vẫn bám sát khi xoay nhanh. Áp dụng trong vòng lặp `main()`.
3. **`GlassesModel`** (class mới) — gộp 1 ảnh chính diện (bắt buộc) + 1 ảnh 3/4
   (tuỳ chọn) thành "1 mẫu kính":
   - Ngưỡng yaw (độ, hằng số lớp, chỉnh được): `YAW_FRONT_ONLY_DEG=14` (chỉ dùng
     chính diện), crossfade dần tới `YAW_BLEND_TO_34_DEG=22` (chuyển hẳn sang
     3/4), giữ 3/4 tới `YAW_FADE_START_DEG=34` (bắt đầu mờ dần **cả kính**), ẩn
     hẳn + hiện gợi ý "Vui lòng nhìn thẳng hơn vào camera" từ `YAW_HIDE_DEG=46`.
   - **Crossfade** thực hiện bằng cách warp riêng từng ảnh ra buffer BGRA
     premultiplied cùng kích thước khung hình (`GlassesOverlay.render_overlay_buffer`,
     tách ra từ `render_on_frame_auto` cũ — đã re-test lại các case Bước A sau
     khi tách, ra kết quả **giống hệt** trước khi tách, không hồi quy), rồi
     `cv2.addWeighted` 2 buffer theo trọng số trước khi blend 1 lần lên khung
     hình thật — đúng kỹ thuật dissolve chuẩn cho ảnh alpha premultiplied.
   - **Lật ảnh 3/4 khi cần** (vấn đề khó nhất): ảnh `_34.png` chỉ quay từ 1
     phía. Tự động quyết định lật hay không bằng cách so **diện tích 2 vùng
     tròng** đo được trong ảnh 3/4 gốc (tròng to hơn = bên gần camera hơn, ít bị
     foreshortening hơn) rồi so với chiều yaw hiện tại. **Đã tự kiểm tra bằng
     ảnh giả lập**: yaw dương ra đúng góc xoay của ảnh gốc, yaw âm ra đúng ảnh
     đã lật ngang **đối xứng chính xác** với yaw dương (xem ảnh test đã xoá sau
     khi kiểm tra).
   - **Đã tự kiểm tra kỹ toàn bộ dải yaw** bằng khung hình giả lập (không cần
     webcam): yaw=0 → 100% chính diện; yaw=16 (trong vùng crossfade 14-22) →
     thấy rõ **cả 2 ảnh chồng mờ lên nhau** đúng hiệu ứng dissolve; yaw=30 →
     100% ảnh 3/4 rõ nét; yaw=38 → ảnh 3/4 **mờ dần** (đúng vùng
     34-46); yaw=50 → **ẩn hẳn + hiện đúng dòng chữ gợi ý**; yaw=-30 → ảnh 3/4
     **lật gương chính xác** so với yaw=+30.
   - **Fallback khi mẫu không có ảnh 3/4**: đã test riêng — không crash, kính
     vẫn hiện đúng ảnh chính diện, mờ dần/ẩn khi yaw lớn giống cơ chế cũ (đúng
     yêu cầu "Xử lý thiếu ảnh" trong mục 13).
   - **Van an toàn cho phần không chắc chắn**: hằng số `GlassesModel.MIRROR_YAW_SIGN`
     (giá trị `1` hoặc `-1`) — nếu test webcam thật thấy ảnh 3/4 lật SAI phía so
     với hướng quay đầu thật, chỉ cần đảo dấu hằng số này là sửa xong, không cần
     sửa logic. Đã ghi rõ trong docstring class.
4. **`discover_glasses_models(glasses_dir)`** — quét `media/tryon/glasses/`,
   gộp file theo quy ước hậu tố `_f.png`/`_34.png` (đúng "Bổ sung Bước B" mục
   13). Mẫu thiếu ảnh `_f` (chính diện) bị bỏ qua kèm cảnh báo; mẫu chỉ có `_f`
   thiếu `_34` vẫn chạy bình thường (fallback đã nói ở trên).
5. **CLI/`main()` cập nhật**:
   - Bỏ mặc định tự động của `--glasses-png` (trước trỏ thẳng 1 file) — giờ mặc
     định là cơ chế quét+gộp mẫu ở trên; in danh sách mẫu tìm được lúc khởi động.
   - Thêm `--glasses-model TEN` (mở sẵn 1 mẫu cụ thể) và phím tắt **`n`** (đổi
     mẫu kế tiếp ngay khi đang xem webcam).
   - `--glasses-png` **vẫn giữ lại** làm lối tắt kiểu cũ (test nhanh 1 file PNG
     đơn, bỏ qua toàn bộ cơ chế quét/3-4) — không phá tính năng debug đã có.
   - HUD thêm dòng hiện `yaw: ±X.X do` và tên mẫu đang dùng — để người dùng tự
     đọc số yaw khi test, hữu ích để đối chiếu nếu `MIRROR_YAW_SIGN` cần đảo.

### Đã tự kiểm tra tổng thể (không webcam)

- `py_compile` sạch; `--help` liệt kê đúng tham số mới.
- Chạy thử toàn bộ `main()` tới bước mở webcam (dùng `--camera-index 99` để cố
  ý báo lỗi mở webcam) — cả 2 mẫu (`Jasmin 01(BL)`, `Vanta 02`) nạp thành công,
  in đúng thông tin tâm tròng + ảnh 3/4 + bên nào gần camera hơn, không
  exception, thoát sạch bằng lỗi mong đợi.

### Việc CHƯA làm — cần người dùng tự test webcam thật

Theo đúng mục 13, DỪNG ở đây chờ xác nhận trực quan (Claude không xem được
webcam nên **không thể tự kiểm chứng phần quan trọng nhất: đúng chiều lật ảnh
3/4 và đúng dấu yaw trên khuôn mặt thật**):

```powershell
.\.venv\Scripts\python.exe prototype\tryon_demo.py
```

Cần xác nhận, theo đúng thứ tự:
1. Nhìn thẳng vào camera → chỉ thấy ảnh chính diện, ổn định (không rung/nhảy).
2. Quay đầu từ từ sang 1 bên → khoảng 15-20° thấy kính bắt đầu **chuyển mờ dần
   sang ảnh 3/4** (không "nhảy" đột ngột), quay tiếp thấy ảnh 3/4 rõ hẳn.
3. **Quan trọng nhất**: ảnh 3/4 hiện ra có **đúng phía** không (ví dụ quay mặt
   sang phải thì phải thấy được nhiều mặt bên phải kính hơn, giống soi gương
   thật) — nếu **BỊ NGƯỢC** (lật sai phía) thì báo lại, tôi chỉ cần đảo dấu
   `GlassesModel.MIRROR_YAW_SIGN` (từ `1` sang `-1`) là sửa xong ngay, không
   cần đổi logic gì thêm.
4. Quay đầu tiếp, gần vuông góc (>~45°) → kính phải **mờ dần rồi ẩn hẳn**, hiện
   dòng chữ "Vui lòng nhìn thẳng hơn vào camera" giữa màn hình.
5. Bấm phím `n` → đổi sang mẫu kính kia (`Vanta 02` hoặc `Jasmin 01(BL)`), lặp
   lại bước 1-4.
6. Đọc số `yaw: ±X.X do` trên HUD khi quay đầu — báo lại nếu số đó có vẻ SAI
   hướng (ví dụ quay phải mà số hiện âm) để đối chiếu thêm với bước 3.

Nếu tất cả ổn → chuyển sang **Bước 2 (mục 11) = Giai đoạn 3 (tối ưu độ trễ)**,
đo bảng FPS trước/sau từng kỹ thuật, baseline hiện tại vẫn là 26.96 FPS (mục 9,
đo trước khi có bất kỳ tối ưu nào — pipeline Bước A/B hiện tại CHƯA tối ưu gì,
có thể chậm hơn baseline vì mỗi khung hình giờ chạy thêm `solvePnP` + có thể
warp 2 ảnh thay vì 1 khi crossfade — việc đo FPS mới thuộc đúng phạm vi Giai
đoạn 3, chưa đo lại trong phiên này).


16 LỖI ẢNH 3/4 & CÁCH KHẮC PHỤC — (ưu tiên làm khi vào phần multi-view)

Triệu chứng quan sát được khi test webcam ở góc yaw ≈ −34.6°: đã đổi sang ảnh 3/4 nhưng kính hiển thị SAI — (a) to quá khổ, (b) lệch sang một bên, (c) càng kính chỉ ngược hướng với hướng đầu đang quay. Đây là 2 lỗi chồng nhau, sửa theo thứ tự.

LỖI 1 — Lật gương sai theo dấu yaw (sửa trước, dễ)

Nguyên nhân: ảnh 3/4 gốc chỉ render cho MỘT phía. Khi người dùng quay sang phía ngược lại, phải lật ngang ảnh cho khớp. Hiện điều kiện "khi nào lật" đang sai dấu yaw (lật nhầm chiều hoặc không lật), nên càng kính chỉ ngược hướng đầu.

Khắc phục:

Chốt quy ước rõ ràng và ghi vào comment: ảnh _34 gốc ứng với đầu quay về phía nào (ví dụ: gốc = quay PHẢI → yaw dương). Từ đó: nếu yaw cùng dấu quy ước → dùng ảnh gốc; nếu ngược dấu → lật ngang (cv2.flip(img,1)).
Khi lật ảnh thì BẮT BUỘC hoán đổi 2 điểm neo trái/phải (tâm tròng gần/xa, điểm tai) theo trục lật — nếu quên, kính dán ngược.
In debug ra màn hình: giá trị yaw, dấu yaw, và trạng thái "CÓ LẬT / KHÔNG LẬT" để mắt thường kiểm chứng quyết định đúng chưa trước khi tinh chỉnh tiếp.
LỖI 2 — Căn ảnh 3/4 bằng công thức của ảnh chính diện → kính phóng to & lệch

Nguyên nhân: cách tự-căn ở Bước A (khoảng cách 2 tròng ↔ khoảng cách 2 mắt) chỉ đúng cho ảnh chính diện. Ở ảnh 3/4, do phối cảnh (foreshortening), 2 tròng bị dồn gần nhau trên ảnh và tâm giữa 2 tròng lệch về phía tròng gần. Dùng khoảng cách 2-tròng (đang nhỏ đi) làm mốc scale → hệ số phóng đại vọt lên → kính bị thổi to; tâm lệch → kính lệch sang một bên. Giả định "ảnh đối xứng/chính diện" bị phá vỡ.

Yêu cầu người dùng (mục tiêu của bước này): khi quay từ góc 3/4 trở đi, áp ảnh kính 3/4 lên mặt, tính theo góc + tọa độ mắt và sống mũi sao cho kính khớp tỉ lệ khuôn mặt và CÙNG KÍCH THƯỚC với mắt, KHÔNG phải chỉnh to/nhỏ tay.

Khắc phục — dùng bộ điểm neo RIÊNG cho ảnh 3/4 (không tái dùng công thức chính diện):

Chọn 2 điểm neo ổn định ở góc nghiêng thay cho "2 tròng":
Trên khuôn mặt (MediaPipe): tâm mắt phía trước (mắt gần camera) và điểm sống mũi / gốc mũi (landmark vùng mũi, ổn định khi quay đầu). Đây là 2 mốc "góc + tọa độ mắt–sống mũi" mà người dùng yêu cầu.
Trên ảnh kính 3/4: tâm tròng phía trước và điểm cầu nối mũi (bridge) của kính. Hai điểm này KHÔNG bị dồn phối cảnh nhiều như cặp "2 tròng".
Tính scale theo tỉ lệ khuôn mặt, không theo khoảng cách 2 tròng: dùng một số đo bền vững của khuôn mặt ở góc nghiêng — ví dụ chiều rộng một mắt (khoé trong ↔ khoé ngoài mắt trước) hoặc khoảng cách mắt trước ↔ sống mũi — rồi đặt bề rộng kính = số đo đó × hệ số cố định (suy 1 lần từ hình học của ảnh, KHÔNG chỉnh tay). Mục tiêu: tròng kính phủ đúng cỡ mắt, không phụ thuộc khoảng-cách-2-tròng đã bị co.
Đặt vị trí bằng cách khớp cặp điểm neo (mắt trước↔tròng trước, sống mũi↔bridge) → ra tịnh tiến + góc; scale lấy từ bước 2. Không dùng width_ratio tay.
One-Euro cho cả yaw, scale, vị trí để không rung/giật khi ở góc nghiêng.
Fallback: nếu không lấy được điểm neo trên ảnh 3/4 → giữ ảnh chính diện + mờ/ẩn theo yaw (không crash). Giữ mọi đường cũ.

Tự kiểm tra trước khi báo xong: render vài khung giả lập ở yaw dương và yaw âm với ảnh 3/4 (và bản lật), xác nhận bằng mắt: kính đúng hướng đầu, cỡ tròng ~ cỡ mắt, tâm không lệch. Rồi DỪNG — người dùng test webcam quay cả hai bên.

Lưu ý thành thật (ghi để cân nhắc)

Ảnh 3/4 chỉ khớp tốt QUANH đúng góc nó được render (~35°); giữa các góc vẫn xấp xỉ. Đây là giới hạn cố hữu của hướng nhiều-ảnh 2D. Vì người dùng đã có file .glb, nên song song vẫn nên cân nhắc thử hướng 3D (three.js) — nơi việc căn góc + lật + cỡ kính được xử lý tự động ở mọi góc, không phải vá riêng cho ảnh 3/4 như mục này.

---

## 17. NHẬT KÝ PHIÊN LÀM VIỆC — sửa Lỗi 1 + Lỗi 2 của mục 16 (căn ảnh 3/4)

Trước khi sửa, đã tra cứu tài liệu/GitHub thật (không đoán) theo đúng yêu cầu người dùng: bài báo EURASIP "Augmented reality virtual glasses try-on technology based on iOS platform" (dùng phép **affine 3 điểm** kiểu "2 tam giác cân tương ứng" giữa mặt và ảnh kính, KHÔNG dùng similarity 2-điểm cứng nhắc), dự án GitHub `alperenuzun/basic-virtual-tryon-glasses` (dùng mô hình 3D + mesh che khuất, không phải ảnh 2D phẳng), và xác nhận qua nhiều nguồn: landmark MediaPipe 133/362 là khoé mắt TRONG (phải/trái). Kết luận rút ra: hướng đi đúng là (a) tách rời việc tính TỶ LỆ khỏi khoảng cách 2 điểm bị phối cảnh bóp méo, và (b) neo vị trí bằng 1 điểm đáng tin cậy thay vì trung điểm 2 điểm bất đối xứng — khớp với đúng hướng người dùng đã đề xuất trong mục 16.

### Đã làm — `prototype/tryon_demo.py`

**Lỗi 1 (lật gương sai chiều)**: giữ nguyên cơ chế `MIRROR_YAW_SIGN` (đảo dấu 1 hằng số nếu sai) đã có sẵn từ mục 15, chỉ **thêm debug HUD** (`GlassesModel._draw_side34_debug`) in trực tiếp lên khung hình: giá trị yaw, trạng thái "CÓ LẬT/KHÔNG LẬT", và bên nào là tròng gần — để người dùng tự đối chiếu bằng mắt khi test, đúng yêu cầu cụ thể của mục 16.

**Lỗi 2 (công thức ảnh chính diện áp sai cho ảnh 3/4)**: viết lại hoàn toàn cách căn ảnh 3/4, KHÔNG dùng `render_overlay_buffer`/`_select_auto_matrix` (Bước A) cho ảnh 3/4 nữa:
- **`FaceMeshDetector.get_eye_centers`** (mới): tâm mỗi mắt = trung điểm khoé ngoài (33/263, đã dùng từ đầu) + khoé trong (133/362, landmark mới, đã xác nhận qua nguồn ngoài) — ổn định hơn 1 điểm khoé ngoài đơn lẻ.
- **`GlassesOverlay._find_lens_anchors_detailed`** mở rộng: trả thêm **bề rộng** mỗi vùng tròng (trước chỉ có tâm + diện tích) — cần cho việc tính hệ số tỷ lệ K.
- **`GlassesOverlay._fixed_scale_matrix`** (mới): ma trận similarity nhưng **tỷ lệ (scale) truyền vào từ bên ngoài**, KHÔNG tự suy từ khoảng cách 2 điểm — chỉ dùng 2 điểm để lấy hướng xoay + 1 điểm neo vị trí tuyệt đối.
- **`GlassesModel`** — logic căn ảnh 3/4 mới, đúng 3 bước người dùng đề xuất ở mục 16:
  1. **Vị trí**: neo thẳng tâm-tròng-GẦN (ảnh 3/4) → tâm-mắt-GẦN (mặt thật, từ `get_eye_centers`) — một cặp điểm duy nhất, không qua trung điểm 2 tròng (nguồn gốc lỗi lệch tâm).
  2. **Góc xoay**: lấy từ hướng vector (tròng-XA − tròng-GẦN) trên ảnh so với (mắt-XA − mắt-GẦN) trên mặt thật — chỉ dùng hướng, không dùng khoảng cách của cặp này làm tỷ lệ.
  3. **Tỷ lệ**: `s_34 = s_front_hiện_tại × K`, với `K = bề_rộng_1_tròng_ảnh_chính_diện / bề_rộng_tròng_gần_ảnh_3-4` tính **một lần lúc nạp ảnh** (chỉ so 2 ảnh PNG tĩnh với nhau, không cần mặt thật) — hoàn toàn không hard-code, và vì `s_front` là tỷ lệ ĐANG CHẠY ĐÚNG của ảnh chính diện (đã được người dùng xác nhận ở Bước A), tròng gần trong ảnh 3/4 sẽ luôn hiện đúng bằng kích thước thật của nó tại đúng khoảng cách mặt-camera hiện tại — không còn "phóng đại" nữa.
  4. **Fallback bắt buộc**: nếu không tính được K (thiếu bề rộng tròng ở ảnh chính diện hoặc ảnh 3/4) → vô hiệu hoá ảnh 3/4 cho mẫu đó ngay lúc nạp (in cảnh báo), quay về dùng ảnh chính diện + mờ/ẩn theo yaw như cũ, không crash.

### Đã tự kiểm tra kỹ (không webcam) — RÚT KINH NGHIỆM QUAN TRỌNG

Lần test đầu dùng điểm giả lập kiểu "đặt tay" (thẳng hàng, khoảng cách tuỳ ý) — **không đủ nghiêm ngặt để bắt lỗi loại này** (chính là cách test cũ ở mục 15 đã bỏ sót vấn đề phối cảnh dẫn đến lỗi mục 16). Lần này viết lại test nghiêm ngặt hơn: dùng **chính công thức `solvePnP` đã kiểm chứng** để xoay một mô hình mặt 3D theo góc yaw biết trước, chiếu xuống 2D bằng camera thật, rồi lấy các điểm mắt/tâm mắt "thực tế có phối cảnh đúng" đó làm đầu vào — thay vì bịa điểm tay. Lần chạy đầu với khoảng cách camera mô phỏng quá gần (kính chiếm hết khung hình) khiến khó đánh giá bằng mắt; đã tự phát hiện, chỉnh lại khoảng cách camera mô phỏng cho thực tế hơn rồi chạy lại.

Kết quả sau khi sửa (ảnh minh hoạ đã xem trực tiếp, không chỉ đọc số):
- yaw=0: kính chính diện khớp mắt bình thường, không đổi hành vi so với Bước A.
- yaw=18 (vùng crossfade): 2 ảnh chồng mờ lên nhau **kích thước khớp nhau**, không còn hiện tượng "giật to" khi bắt đầu chuyển ảnh.
- yaw=25, 30 (ảnh 3/4 rõ nét): tròng gần khớp đúng tâm mắt gần, kích thước hợp lý theo tỉ lệ khuôn mặt hiện tại — đã hết cả 2 triệu chứng "phóng to" và "lệch tâm" của mục 16.
- yaw=-25, -30: đúng bản đã lật gương, đối xứng chính xác với yaw dương, debug HUD in đúng "CÓ LẬT".
- Test lại cả 2 mẫu (`Jasmin 01(BL)` — trường hợp Otsu, `Vanta 02` — trường hợp lỗ thật) đều cho kết quả đúng tương tự.
- Test riêng mẫu không có ảnh 3/4 (`has_side34=False`) qua toàn dải yaw — không exception, không crash.
- Đã chạy lại nguyên bộ test hồi quy Bước A (`render_jasmin_*`, `render_vanta_*`, `render_fallback_demo_glasses`) — **kết quả giống hệt trước khi sửa**, không ảnh hưởng đến đường chính diện.
- `py_compile` sạch; chạy thử `main()` toàn bộ tới bước mở webcam (`--camera-index 99`) — nạp đúng cả 2 mẫu, in đúng hệ số K (`Jasmin 01(BL)`: K=0.833, `Vanta 02`: K=1.195), không exception.

### Việc CHƯA làm — cần người dùng tự test webcam thật

DỪNG ở đây theo đúng yêu cầu mục 16 ("người dùng test webcam quay cả hai bên"):

```powershell
.\.venv\Scripts\python.exe prototype\tryon_demo.py
```

Cần xác nhận: (1) tròng gần có khớp đúng cỡ mắt không, không còn phóng to/lệch; (2) hướng lật ảnh 3/4 có đúng chiều đầu quay không (đọc dòng debug `[debug 3/4]` màu tím nhạt ở gần đáy khung hình để đối chiếu); (3) chuyển tiếp chính diện↔3/4 có mượt không. Nếu vẫn còn lệch, báo cụ thể + số yaw lúc đó để chẩn đoán tiếp.

---

## 18. NHẬT KÝ PHIÊN LÀM VIỆC — ĐỔI HƯỚNG: xoá toàn bộ ảnh 3/4, thử "tự vẽ gọng theo landmark"

Người dùng chủ động đổi hướng thay vì tiếp tục vá mục 16/17: **xoá sạch toàn bộ cơ chế
ảnh 3/4 tĩnh + crossfade + lật gương + hệ số K** (đã hoạt động nhưng người dùng muốn
thử hướng khác trước). Yêu cầu cụ thể: mỗi mắt tự lấy tròng kính thật từ PNG chính
diện, tính toán tọa độ theo landmark khi xoay đầu, còn gọng nối giữa 2 tròng (cầu mũi)
và càng kính thì **tự vẽ** — không cần ảnh góc nghiêng riêng nữa. Đây là bước thử
nghiệm ("nếu ổn thì làm tiếp"), không phải quyết định chốt cuối cùng.

### Đã xoá khỏi `prototype/tryon_demo.py`

Toàn bộ `class GlassesModel` cũ (side34_asis/side34_mirrored, `_load_side34`,
`_pick_side34`, `_render_side34_buffer`, `MIRROR_YAW_SIGN`, `_subject_right_is_near`,
`_draw_side34_debug`, các ngưỡng `YAW_FRONT_ONLY_DEG`/`YAW_BLEND_TO_34_DEG`, hệ số K),
`GlassesOverlay._fixed_scale_matrix`, phần gom cặp `_f`/`_34` trong
`discover_glasses_models`/`load_glasses_models`. `GlassesOverlay` (Bước A — tự động
căn kính 1 tấm ảnh chính diện, đã được người dùng xác nhận "định vị khá tốt") **giữ
nguyên hoàn toàn**, không đụng vào.

### Đã thêm — cơ chế mới (tạm gọi Bước C)

1. **`FaceMeshDetector.get_eye_widths`** (mới): khoảng cách khoé ngoài↔khoé trong của
   từng mắt (dùng landmark 33/133 và 263/362 đã có sẵn) — tín hiệu "mắt này đang rộng
   hay đang bị phối cảnh bóp lại" theo từng mắt riêng biệt.
2. **`GlassesOverlay._set_image`** mở rộng: khi tự tìm được 2 tâm tròng, cắt luôn ảnh
   thành **2 "nửa" trái/phải** (che alpha=0 nửa kia, giữ nguyên kích thước canvas) để
   sau này warp độc lập từng mắt; đồng thời lưu **bề rộng từng tròng** (đã có từ mục
   17) và **màu gọng** (`_estimate_frame_color` — lấy màu trung vị 1 vành mỏng sát viền
   ngoài silhouette, dùng logic đã kiểm chứng ở mục 17) để phần tự vẽ dùng đúng màu.
3. **`GlassesOverlay._select_auto_matrix`** sửa: giờ trả thêm cờ `swapped` (tròng trái
   PNG khớp mắt phải hay mắt trái giải phẫu) — trước đây thông tin này bị giấu bên
   trong, giờ `GlassesModel` cần biết chính xác để không gán nhầm tròng cho mắt.
4. **`GlassesOverlay._pinned_matrix`** (mới, thay `_fixed_scale_matrix` đã xoá): ma
   trận xoay+tỷ lệ+tịnh tiến với **góc và tỷ lệ truyền sẵn từ ngoài**, chỉ ghim đúng 1
   cặp điểm (tâm tròng → tâm mắt) — dùng để warp riêng từng mắt.
5. **`GlassesOverlay._composite_over`** (mới): công thức Porter-Duff "over" tổng quát
   (cả RGB lẫn alpha) để ghép 2 nửa mắt đã warp độc lập lại với nhau.
6. **`GlassesModel`** viết lại hoàn toàn — thuật toán mỗi khung hình:
   - Lấy ma trận + góc nghiêng (roll) + tỷ lệ hiện tại từ chính phép biến đổi Bước A
     (dùng chung 1 góc cho cả 2 mắt, tránh vác lệch nhau).
   - Tính tỷ lệ **riêng cho từng mắt**: chênh lệch bề rộng 2 mắt chuẩn hoá theo tỷ số
     `(rộng_a − rộng_b)/(rộng_a + rộng_b)` (luôn trong [-1,1], không "nổ" khi 1 bên tiến
     về 0 như phép chia trực tiếp), nhân hệ số `K_PERSPECTIVE=0.7`. Ở góc thẳng, 2 tỷ lệ
     bằng nhau và bằng đúng Bước A — không đổi hành vi khi nhìn thẳng.
   - Warp độc lập 2 nửa ảnh, ghép lại bằng `_composite_over`.
   - **Tự vẽ** cầu mũi + 2 càng kính (`_draw_bridge_and_temples`) nối 2 mắt vừa warp,
     toạ độ tính trực tiếp từ tâm mắt/bề rộng mắt — càng kính dài/ngắn theo đúng bề
     rộng mắt của chính bên đó nên bên xa tự ngắn lại khi quay đầu (phối cảnh tự nhiên,
     không cần tính riêng).
   - Yaw (solvePnP) **chỉ còn dùng để an toàn** (mờ dần rồi ẩn khi góc quá lớn,
     ngưỡng nới rộng ra 45°/60° so với bản cũ 34°/46° vì cơ chế mới không còn giới hạn
     bởi "chỉ đúng quanh 1 góc render sẵn" nữa) — không còn dùng để chọn/lật ảnh.

### Lỗi tự phát hiện và sửa trong lúc tự kiểm tra (quan trọng)

- **Lần test đầu dùng điểm thẳng hàng đặt tay** → không phát hiện được vấn đề gì đặc
  biệt, nhưng đây chính là kiểu test yếu đã bỏ sót lỗi ở mục 16 trước đó, nên đã chuyển
  sang dùng lại cách mô phỏng `solvePnP` thực tế (xoay mặt 3D theo góc biết trước,
  chiếu xuống 2D) làm chuẩn.
- **Đường tự vẽ bị trùng/thừa ở góc gần thẳng (yaw≈0)**: lúc 2 mắt gần như đối xứng, 2
  nửa ảnh ghép lại khít y hệt Bước A (gọng thật trong PNG đã đủ liền mạch) — vẽ thêm
  đường nữa tạo hiệu ứng "đường kẻ đôi" xuyên ngang khung hình. **Sửa**: chỉ tự vẽ khi
  `|diff_ratio| > 0.05` (2 mắt đã lệch tỷ lệ đáng kể, tức đã có "khe hở" thật sự cần
  lấp) — hằng số `PROCEDURAL_DRAW_THRESHOLD`.
- **Đường tự vẽ xuất phát từ TÂM mắt, cắt xuyên qua giữa tròng kính** (trông như "que
  xiên qua kính") — do ban đầu lấy `center` làm điểm bắt đầu trực tiếp. **Sửa**: tính
  điểm "mép tròng" (trong/ngoài) bằng nửa bề rộng tròng thật (đã nhân tỷ lệ hiện tại)
  offset từ tâm mắt, cầu mũi nối 2 mép TRONG, càng kính xuất phát từ mép NGOÀI — phát
  hiện thêm 1 lỗi dấu khi làm bước này (mép ngoài tính nhầm thành mép trong), đã sửa và
  xác nhận lại bằng ảnh crop phóng to.

### Đã tự kiểm tra (không webcam, ảnh minh hoạ đã xem trực tiếp)

- `py_compile` sạch; chạy lại nguyên bộ test hồi quy Bước A — **kết quả giống hệt**
  trước khi đổi hướng (không đụng `GlassesOverlay.render_on_frame_auto`).
- Test mới dùng điểm `solvePnP` thực tế trên cả 2 mẫu kính, dải yaw 0→50°/-40°: yaw=0
  khớp Bước A y hệt (không có đường thừa); yaw=20-40° tròng 2 bên co giãn nhẹ theo
  đúng chiều gần/xa, cầu mũi ghép liền mạch với gọng thật của PNG (đã soi ảnh crop
  phóng to, chỉ có 1 vệt răng cưa nhỏ ở chỗ nối, không đáng kể); yaw=-40° đối xứng
  chính xác với +40° (không cần logic lật riêng — tự động vì mọi thứ suy từ landmark
  sống); yaw=50° (qua ngưỡng mờ dần 45°) mờ đúng như thiết kế; không exception ở bất kỳ
  góc nào.
- Chạy lại `main()` đầy đủ tới bước mở webcam (`--camera-index 99`) — nạp đúng 2 mẫu,
  không exception.

### Điểm CHƯA chắc chắn — thành thật báo trước khi người dùng test

- **Độ mạnh/chiều của hiệu ứng "mắt gần to hơn mắt xa"**: mô hình mặt 3D dùng để tự
  test (toạ độ khoé mắt TRONG là tôi tự ước lượng gần đúng, không có nguồn xác thực
  như toạ độ khoé mắt NGOÀI đã dùng từ Bước A) cho ra chênh lệch khá NHỎ (~5-10% ở góc
  40-50°) và ở 1 vài mốc còn cho chiều **ngược lại trực giác** (mắt gần lại hiện nhỏ
  hơn mắt xa) — nhiều khả năng do toạ độ khoé mắt trong tôi tự ước lượng chưa chuẩn
  (ảnh hưởng bài test, không hẳn ảnh hưởng thuật toán thật vì code thật dùng landmark
  MediaPipe sống, không dùng toạ độ tôi bịa) nhưng **không loại trừ đây là hạn chế thật
  của việc dùng "bề rộng mắt" làm tín hiệu phối cảnh**. Cần xem trên mặt thật mới biết
  chắc — nếu hiệu ứng quá yếu/sai chiều, chỉnh `GlassesModel.K_PERSPECTIVE` (tăng nếu
  yếu, đổi dấu nếu ngược chiều) là sửa nhanh được, không cần đổi kiến trúc.
- **Càng kính** giờ là đường thẳng vector đơn giản (không còn chi tiết bản lề/hoạ tiết
  thật như ảnh chụp) — trông sẽ "giản lược" hơn hẳn so với hướng ảnh 3/4 cũ ở phần này,
  đổi lại được cái lợi là phản ứng liên tục mọi góc, không cần ảnh phụ.

### Việc CHƯA làm — cần người dùng tự test webcam thật

DỪNG ở đây theo đúng yêu cầu "thử trước, nếu ổn thì làm tiếp":

```powershell
.\.venv\Scripts\python.exe prototype\tryon_demo.py
```

Cần đánh giá: (1) khi quay đầu, tròng kính có TỰ NHIÊN co giãn theo mắt không hay trông
cứng/giật; (2) tròng gần có thấy TO HƠN tròng xa một cách hợp lý không (đây là điểm
CHƯA chắc chắn ở trên — nếu ngược chiều hoặc quá yếu, báo lại để chỉnh
`K_PERSPECTIVE`); (3) cầu mũi/càng kính tự vẽ có hoà hợp được với phần ảnh thật của
tròng kính không, hay lộ rõ là hình vẽ vector tách biệt; (4) tổng thể có "chân thật" đủ
để tiếp tục đầu tư thêm không, hay quay lại hướng ảnh 3/4 cũ (đã hoạt động, chỉ là kém
liên tục giữa các góc) sẽ tốt hơn.

---

## 19. NHẬT KÝ PHIÊN LÀM VIỆC — UNDO: khôi phục về cuối Bước A (bỏ hướng mục 18)

Người dùng test webcam thật hướng "tự vẽ gọng theo landmark" (mục 18) và báo **"không
ổn"** — không đi vào chi tiết cụ thể lệch ở đâu, chỉ yêu cầu **undo hoàn toàn** về đúng
trạng thái cuối Bước A (mục 14 — thời điểm người dùng đã xác nhận "kính định vị khá
tốt"), để sau đó làm lại bước xử lý nghiêng đầu theo hướng khác.

### Vấn đề khi undo

Repo **không có commit nào** cho các thay đổi này (`git status` cho thấy toàn bộ
`prototype/` và `CLAUDE_PROGRESS.md` ở dạng `??` — chưa từng add/commit), nên không thể
`git checkout`/`git revert` thẳng. Đã hỏi lại người dùng xác nhận đúng điểm mốc cần về
(cuối mục 14) trước khi thao tác, vì đây là hành động khó đảo ngược nếu hiểu sai mốc.

### Đã làm — khôi phục thủ công `prototype/tryon_demo.py` về đúng trạng thái cuối mục 14

Vì không có snapshot git, đã khôi phục bằng cách **gỡ bỏ tuần tự** từng phần được thêm
ở mục 15/17/18 (không retype lại từ đầu, giảm rủi ro gõ sai), dựa trên chính nội dung
"before/after" còn lưu trong lịch sử chỉnh sửa của phiên:
- Xoá `class OneEuroFilter`.
- `FaceMeshDetector`: gỡ `RIGHT_EYE_INNER`/`LEFT_EYE_INNER`, `_POSE_MODEL_POINTS`,
  `get_eye_centers`, `get_eye_widths`, `estimate_yaw_deg` — chỉ còn `RIGHT_EYE_OUTER`/
  `LEFT_EYE_OUTER`, `get_eye_anchor_points` như nguyên bản.
- `GlassesOverlay`: gỡ `from_bgra`, các trường `_left_masked_premult`/
  `_right_masked_premult`/`_lens_left_width`/`_lens_right_width`/`_frame_color`,
  `_estimate_frame_color`, `_select_auto_matrix`/`render_overlay_buffer`/
  `_warp_to_frame_buffer`/`_pinned_matrix`/`_composite_over`. Gộp `_find_lens_anchors_detailed`
  trở lại thành 1 hàm `_find_lens_anchors` duy nhất (bỏ diện tích/bề rộng, chỉ trả toạ
  độ tâm). `render_on_frame_auto` trở lại bản inline gốc (tự tính ma trận + warpAffine +
  blend trực tiếp, không qua các hàm phụ).
- Xoá hẳn `class GlassesModel`, `discover_glasses_models`, `load_glasses_models`; khôi
  phục lại `_default_glasses_png()`.
- `main()` khôi phục nguyên bản: chỉ dùng `GlassesOverlay` trực tiếp qua `--glasses-png`
  (mặc định tự quét file `_f.png` đầu tiên), không còn multi-model/`--glasses-model`/phím
  `n`, không còn yaw/eye-centers/eye-widths.
- Docstring đầu file và class `GlassesOverlay` cũng đổi lại đúng mô tả chỉ-Bước-A.

### Đã tự kiểm tra sau khi khôi phục

- `py_compile` sạch.
- `grep` xác nhận **không còn** bất kỳ vết tích nào của `GlassesModel`, `OneEuroFilter`,
  `estimate_yaw_deg`, `get_eye_centers`, `get_eye_widths`, `discover_glasses_models`,
  `load_glasses_models`, `_pinned_matrix`, `_composite_over`, `_select_auto_matrix`,
  `_find_lens_anchors_detailed` trong file.
- Chạy lại đúng bộ test hồi quy Bước A đã dùng xuyên suốt từ mục 14 — **kết quả giống
  hệt** (căn kính tự động, đổi chỗ eye_a/eye_b không đổi kết quả, nghiêng đầu xoay đúng
  chiều, fallback vẫn hoạt động).
- `--help` cho ra đúng 7 tham số y hệt mục 14 (không còn `--glasses-model`), mặc định
  `--glasses-png` tự trỏ đúng `Jasmin 01(BL)_f.png`.
- Chạy thử `main()` tới bước mở webcam (`--camera-index 99`) — thứ tự thực thi đúng bản
  gốc (kiểm tra webcam THẤT BẠI ngay, thoát TRƯỚC KHI nạp ảnh kính — khác voi ban muc
  15+ von nap models truoc), không exception.

### Trạng thái hiện tại

`prototype/tryon_demo.py` hiện đúng bằng trạng thái đã được người dùng duyệt ở mục 14
("kính định vị khá tốt"). Mục 13 (prompt gốc cho phiên tiếp theo) vẫn còn nguyên — Bước
B (đổi ảnh theo góc quay đầu) coi như **CHƯA làm lại**, cả 2 hướng đã thử (ảnh 3/4 tĩnh
ở mục 15/17, và tự vẽ gọng theo landmark ở mục 18) đều bị người dùng từ chối/undo. Chờ
người dùng chỉ đạo hướng tiếp theo cho bài toán nghiêng đầu trước khi code tiếp — KHÔNG
tự ý chọn lại 1 trong 2 hướng cũ hoặc bắt đầu hướng thứ 3 mà chưa hỏi.

**Lưu ý thành thật (giữ nguyên từ mục 16, vẫn đúng)**: đây vẫn là giải pháp 2D-nhiều-ảnh, chỉ khớp tốt NHẤT quanh đúng góc ảnh `_34` được render — giữa các góc là xấp xỉ hình học hợp lý chứ không phải chính xác tuyệt đối (giới hạn cố hữu, không phải bug). Người dùng đã có file `.glb` (mô hình 3D) — nếu muốn chính xác ở MỌI góc mà không cần vá thêm, hướng 3D (dùng .glb, dựng trong three.js hoặc render 3D phía server) là lựa chọn triệt để hơn về lâu dài, nhưng đó là **thay đổi kiến trúc lớn** (khác hẳn quyết định #1 ở mục 2 — xử lý ảnh phía server bằng OpenCV/Python) nên cần bàn lại với người dùng trước khi làm, không tự ý chuyển hướng.

### 20.PROMPT — Bảng chọn kính ngay trên cửa sổ webcam (glasses picker)

Mục tiêu: hiển thị các mẫu kính đang có ngay trên màn hình webcam; người dùng chọn mẫu nào thì áp mẫu đó lên mặt NGAY, không cần khởi động lại. Số lượng mẫu là TỰ ĐỘNG theo số ảnh trong thư mục (KHÔNG hard-code). Tính năng này dùng cho cả 2D lẫn 3D. Làm xong tự kiểm tra, DỪNG chờ người dùng test webcam. Comment tiếng Việt.

Nguồn danh sách mẫu
Quét thư mục ảnh kính, gom theo quy ước tên ở mục 13 (<ten>_f.png / <ten>_34.png) → ra danh sách các mẫu. Bao nhiêu mẫu thì bấy nhiêu lựa chọn.
Mỗi mẫu tối thiểu phải có ảnh _f. Mẫu thiếu _f → bỏ khỏi danh sách + cảnh báo.
Tính sẵn thumbnail (ảnh _f thu nhỏ, ví dụ cao ~70px) và cache một lần khi nạp, không tạo lại mỗi khung hình.
Hiển thị trên cửa sổ webcam
Vẽ một dải thumbnail dọc theo cạnh dưới (hoặc trên) khung hình: mỗi ô là ảnh kính thu nhỏ + số thứ tự + tên mẫu.
Mẫu đang chọn: vẽ viền sáng / nền nổi bật để phân biệt.
Nếu số mẫu nhiều hơn số ô hiển thị vừa màn hình: cho cuộn dải (phím ,/. hoặc mũi tên trái/phải) thay vì tràn ra ngoài.
Vẽ dải phải nhẹ, không làm tụt FPS (blend ô thumbnail đã cache, không xử lý nặng).
Cách chọn (hỗ trợ cả hai)
Phím số 1..9 → chọn nhanh mẫu tương ứng đang hiển thị. (Nếu >9 mẫu thì kết hợp cuộn dải rồi bấm số trong trang hiện tại.)
Chuột click vào ô thumbnail (cv2.setMouseCallback) → chọn mẫu đó.
Khi chọn: nạp bộ ảnh của mẫu (dùng cache đã có ở mục 13), áp lên mặt ngay ở khung kế tiếp. Không khởi động lại chương trình.
Xử lý & kiểm tra
0 mẫu trong thư mục → hiển thị thông báo "Chưa có mẫu kính", không crash.
Giữ nguyên các phím cũ (thoát q, và phím chỉnh tay +/-/[/] nếu còn dùng làm fallback).
Tự kiểm tra: chạy thử, xác nhận: dải thumbnail hiện đúng số mẫu; bấm số / click đổi được kính; kính mới áp đúng lên mặt; FPS không tụt đáng kể.

DỪNG — người dùng test webcam: có bao nhiêu mẫu hiện ra, chọn qua lại có mượt không.

Ghi chú cho Giai đoạn 5 (Django)

Dải thumbnail + chọn bằng phím/chuột này ở prototype sẽ chuyển thành gallery HTML trên trang thử kính (click thumbnail để đổi kính, KHÔNG tải lại trang) như yêu cầu ở mục 7. Logic "gom mẫu theo tên + nạp bộ ảnh khi chọn" tái dùng được; chỉ đổi phần hiển thị từ cửa sổ OpenCV sang HTML/JS.

---

## 21. NHẬT KÝ PHIÊN LÀM VIỆC — hoàn thành mục 20 (bảng chọn kính trên webcam)

### Đã làm — `prototype/tryon_demo.py`

1. **`discover_glasses_models(glasses_dir)`** (đưa lại, đơn giản hơn bản mục 15 cũ vì
   không còn cần gộp cặp `_f`/`_34`): quét `*_f.png`, tên mẫu = tên file bỏ hậu tố `_f`.
   Số lượng mẫu **hoàn toàn tự động** theo số file, không hard-code.
2. **`class GlassesPicker`** (mới, tách hẳn khỏi `GlassesOverlay` — không đụng code Bước
   A đã ổn định):
   - Nạp **sẵn** toàn bộ mẫu thành `GlassesOverlay` + 1 **thumbnail** (ảnh PNG ghép lên
     nền xám cố định, resize cao 70px) ngay lúc khởi tạo — chỉ tính **một lần**, không
     tính lại mỗi khung hình (đúng yêu cầu giữ FPS ổn định).
   - `draw(frame)`: vẽ dải thumbnail sát đáy khung hình — mỗi ô gồm thumbnail + số thứ
     tự + tên mẫu, viền xanh lá cho mẫu đang chọn, viền xám cho mẫu khác. Chỉ thao tác
     copy mảng + vẽ hình chữ nhật/chữ đơn giản trên ảnh đã cache, không xử lý ảnh nặng
     trong vòng lặp chính.
   - Hỗ trợ **cuộn dải** (`scroll()`, giới hạn không cuộn quá đầu/cuối) khi số mẫu nhiều
     hơn số ô vừa màn hình — có mũi tên `<`/`>` báo hiệu còn mẫu ngoài vùng hiện.
   - `select_visible_slot(slot)`: ánh xạ đúng phím số 1-9 sang mẫu thực (tính luôn phần
     đã cuộn) — không lấy nhầm mẫu khi đang cuộn dở.
   - `handle_mouse_click(x, y)`: dò toạ độ click với các ô đã vẽ ở lần `draw()` **gần
     nhất** (lưu `_cell_rects`) để chọn đúng mẫu, click ngoài dải thì bỏ qua.
   - 0 mẫu (thư mục rỗng hoặc tất cả lỗi nạp) → `current_overlay` trả `None`,
     `draw()` chỉ hiện 1 dòng cảnh báo, không crash — `main()` luôn tự kiểm tra `None`
     trước khi gọi render, không giả định luôn có ít nhất 1 mẫu.
3. **`main()`** cập nhật:
   - Mặc định (không truyền `--glasses-png`) quét cả thư mục, dựng `GlassesPicker` cho
     toàn bộ mẫu tìm được. `--glasses-png` (kiểu cũ) vẫn giữ làm lối tắt bỏ qua bảng
     chọn, dựng picker với đúng 1 mẫu "custom" — thống nhất 1 đường code duy nhất, không
     phải rẽ nhánh riêng cho 2 trường hợp.
   - `cv2.namedWindow` + `cv2.setMouseCallback` (hàm `_picker_mouse_callback`, nhận
     `picker` qua tham số `param`, không dùng biến toàn cục) gắn **trước** vòng lặp.
   - Thêm phím `1`-`9` (chọn nhanh), `,`/`.` (cuộn dải) — theo đúng yêu cầu mục 20 (bỏ
     qua hỗ trợ phím mũi tên vì mã phím mũi tên qua `cv2.waitKey` không thống nhất giữa
     các nền tảng/bản OpenCV, không muốn đoán mà không kiểm chứng được — mục 20 cho phép
     dùng `,`/`.` HOẶC mũi tên, chỉ cần 1 trong 2 là đủ).
   - Các dòng HUD cũ (cảnh báo "không phát hiện khuôn mặt", gợi ý calibration) được **đẩy
     lên trên** đúng bằng chiều cao dải thumbnail (`GlassesOverlay.draw_calibration_hint`
     thêm tham số `bottom_margin`) để không bị dải thumbnail đè lên.
   - Xoá `_default_glasses_png()` (không còn nơi nào gọi — bảng chọn đã thay thế đúng
     mục đích của nó).

### Đã tự kiểm tra kỹ (không cần webcam, theo đúng thói quen xuyên suốt)

- `py_compile` sạch; xác nhận `cv2.EVENT_LBUTTONDOWN`/`setMouseCallback`/`namedWindow`
  tồn tại đúng trong bản OpenCV cài trong venv (không đoán API).
- Test `GlassesPicker` bằng khung hình giả lập (không webcam):
  - Nạp đúng 2 mẫu thật trong thư mục, vẽ dải — xem ảnh: thumbnail rõ, viền xanh lá
    đúng mẫu đang chọn, tên/số thứ tự đọc được.
  - `select_visible_slot(1)` đổi đúng sang mẫu thứ 2.
  - Mô phỏng click chuột đúng toạ độ tâm ô đầu tiên → chọn đúng mẫu đó (assert PASS);
    click ra ngoài dải → không đổi lựa chọn (assert PASS).
  - Giả lập 12 mẫu (lặp lại 2 ảnh thật) để ép phải cuộn: hiện đúng 7 ô vừa khung 800px,
    mũi tên `>` xuất hiện đúng lúc; cuộn 1 nấc rồi bấm phím số 9 → ra đúng mẫu tại vị trí
    `scroll_offset + 8`, không lấy nhầm.
  - 0 mẫu: `current_overlay` là `None`, `draw()`/`handle_mouse_click()`/
    `select_visible_slot()` đều không crash.
  - Ghép chung 1 khung: kính đeo lên mặt giả lập + toàn bộ HUD (yaw ví dụ, tên mẫu,
    trạng thái calibration) + dải thumbnail cùng lúc — xem ảnh xác nhận **không dòng nào
    đè lên dải thumbnail**.
- Chạy `main()` đầy đủ tới bước mở webcam (`--camera-index 99`) ở **cả 2 chế độ**: mặc
  định (quét thư mục, in đúng danh sách 2 mẫu) và `--glasses-png` (kiểu cũ, nạp đúng 1
  file) — không exception ở chế độ nào.
- `--help` hiển thị đúng, mô tả rõ `--glasses-png` giờ là lối tắt "bỏ qua bảng chọn".

### Điều CHƯA thể tự kiểm tra (thành thật)

FPS thực tế khi bật dải thumbnail chỉ có thể đo được trên webcam thật (môi trường này
không có webcam/màn hình). Đã cân nhắc kỹ về mặt thiết kế: `draw()` mỗi khung hình chỉ
copy mảng thumbnail đã cache + vài lệnh `cv2.rectangle`/`cv2.putText` cho tối đa ~7 ô —
rẻ hơn nhiều so với suy luận MediaPipe + CLAHE đã chạy sẵn mỗi khung hình, nên tin tưởng
hợp lý là không tụt FPS đáng kể, nhưng **chưa đo được số thật**.

### Việc CHƯA làm — cần người dùng tự test webcam thật

DỪNG ở đây theo đúng yêu cầu mục 20:

```powershell
.\.venv\Scripts\python.exe prototype\tryon_demo.py
```

Cần xác nhận: (1) dải thumbnail hiện đúng số mẫu (hiện có 2: Jasmin 01(BL), Vanta 02);
(2) bấm phím `1`/`2` và click chuột vào từng ô đều đổi kính đúng, áp lên mặt ngay không
cần khởi động lại; (3) FPS hiển thị trên HUD có tụt rõ rệt so với trước khi có dải
thumbnail không; (4) các dòng chữ HUD khác có bị dải thumbnail che mất không.


### 22. PROMPT — Đổi bảng chọn kính sang CỘT DỌC bên phải, cuộn bằng lăn chuột / phím lên-xuống

Bảng chọn kính ở mục 15 đã chạy tốt (hiện đúng số mẫu, click/số đổi được kính). Yêu cầu mới: đổi bố cục dải thumbnail từ nằm ngang dưới đáy → cột dọc ở cạnh phải màn hình, và cho cuộn khi nhiều mẫu. GIỮ nguyên logic gom mẫu + chọn + áp kính; chỉ đổi phần vẽ và cách cuộn. Comment tiếng Việt. Tự kiểm tra, DỪNG chờ người dùng test webcam.

Bố cục mới
Xếp thumbnail thành một cột dọc sát cạnh phải khung hình: các ô xếp từ trên xuống, mỗi ô = ảnh kính thu nhỏ + số thứ tự + tên mẫu; ô đang chọn viền sáng.
Tránh đè lên vùng debug/ROI bên phải (ô khung vàng trong ảnh hiện tại): hoặc đặt cột kính vào một dải lề riêng, hoặc chỉ bật vùng debug khi cần — KHÔNG để hai thứ chồng lên nhau. Nếu cần, thu hẹp vùng debug hoặc cho bật/tắt nó bằng một phím.
Cột chỉ hiển thị được N ô vừa chiều cao màn hình; phần dư thì cuộn (xem dưới).
Cuộn danh sách
Lăn chuột (cv2.setMouseCallback, sự kiện EVENT_MOUSEWHEEL): lăn xuống → cuộn danh sách xuống, lăn lên → cuộn lên.
Phím mũi tên lên/xuống (hoặc w/s nếu mã phím mũi tên khó bắt trên OpenCV Windows — tự kiểm tra cv2.waitKeyEx trả mã nào rồi map cho đúng): di chuyển ô đang chọn lên/xuống; khi ô chọn ra ngoài vùng nhìn thấy thì tự cuộn theo để nó luôn hiện.
Nếu số mẫu ít hơn số ô hiển thị được thì không cuộn (bỏ qua thao tác cuộn).
Vẽ gợi ý nhỏ (mũi tên ▲▼ hoặc thanh cuộn mảnh) để người dùng biết còn mẫu phía trên/dưới.
Giữ nguyên & kiểm tra
Vẫn chọn được bằng click vào ô và bằng phím số (số ứng với ô đang hiển thị trong cột). Chọn xong áp kính ngay.
Thumbnail vẫn dùng cache (mục 15), cuộn không được tạo lại thumbnail → không tụt FPS.
Cập nhật dòng tiêu đề/hướng dẫn phím cho khớp bố cục mới.
Tự kiểm tra: nhiều mẫu (thử tạo tạm vài mẫu) để thấy cuộn hoạt động; lăn chuột và phím lên/xuống đều cuộn đúng; ô chọn luôn nằm trong vùng nhìn thấy; FPS không tụt.

DỪNG — người dùng test webcam: cột kính bên phải cuộn bằng lăn chuột và phím lên/xuống có mượt không, có đè vùng debug không.

Ghi chú Django (Giai đoạn 5)

---

## 23. NHẬT KÝ PHIÊN LÀM VIỆC — hoàn thành mục 22 (bảng chọn kính đổi sang cột dọc bên phải)

Người dùng gọi đây là "mục 21" nhưng số đó tôi đã dùng cho log hoàn thành mục 20 —
nội dung PROMPT thực tế nằm ở mục 22 trong file (đổi bảng chọn từ dải ngang sang cột
dọc). Không có prompt nào khác chưa xử lý nên đã làm thẳng mục 22, không hỏi lại.

### Đã tra cứu trước khi code (không đoán API)

- `cv2.getMouseWheelDelta` — hàm chính thức để giải mã lăn chuột — **không có** trong
  binding Python của bản OpenCV 5.0.0 đang cài (`hasattr(cv2, 'getMouseWheelDelta')` =
  `False`, xác nhận thêm bằng cách tìm trong file `.pyi` đi kèm gói — không có). Phải tự
  giải mã thủ công từ `flags` theo đúng quy ước Win32 `GET_WHEEL_DELTA_WPARAM` (16 bit
  cao là số có dấu) mà OpenCV kế thừa — đã đối chiếu với tài liệu chính thức (delta là
  bội số của 120) và **tự kiểm chứng bằng flags giả lập** đúng quy ước đó (xem phần test).
- `cv2.EVENT_MOUSEWHEEL`, `cv2.waitKeyEx` — xác nhận tồn tại đúng trong bản cài.
- Mã phím mở rộng (`waitKeyEx`) cho mũi tên lên/xuống trên Windows — dùng giá trị được
  nhiều tài liệu/ví dụ OpenCV độc lập trích dẫn thống nhất (2490368/2621440), nhưng
  **không có màn hình/bàn phím thật để tự bấm kiểm chứng trong môi trường này** — đúng
  như mục 22 đã lường trước, nên `w`/`s` được cài làm phương án chắc chắn hoạt động
  song song (đã kiểm chứng qua `waitKey` bình thường, không phụ thuộc giả định mã phím).

### Xung đột phát hiện khi code: phím `s`

Phím `s` cũ dùng để "in calibration ra console" (chế độ dự phòng) trùng với `s` mới
dùng để di chuyển xuống trong cột kính. Đã đổi phím in calibration cũ sang `p` (in),
cập nhật đồng bộ ở `draw_calibration_hint`, HUD, docstring đầu file, và
`CLAUDE_PROGRESS.md` này — tránh 1 phím làm 2 việc khác nhau.

### Đã làm — `prototype/tryon_demo.py`

1. **`GlassesPicker`** — GIỮ NGUYÊN toàn bộ logic gom mẫu/chọn/áp kính (`models`,
   `select`, `select_visible_slot`, `current_overlay`, `current_name`) như mục 20, chỉ
   đổi phần hiển thị và cuộn:
   - Hằng số đổi từ `STRIP_HEIGHT`/`CELL_WIDTH` (dải ngang) sang `COLUMN_WIDTH` (140px),
     `THUMB_MAX_HEIGHT`, `CELL_HEIGHT`, `TOP_MARGIN` (cột dọc).
   - `_make_thumbnail` viết lại: thu nhỏ theo kiểu "contain" (giữ tỉ lệ, vừa khít khung
     `(COLUMN_WIDTH-2*PADDING) x THUMB_MAX_HEIGHT`, không méo hình như bản cũ ép cứng
     chiều cao), dán CHÍNH GIỮA 1 canvas nền xám KÍCH THƯỚC CỐ ĐỊNH — `draw()` nhờ vậy
     chỉ cần copy thẳng canvas, không phải tính offset riêng mỗi thumbnail mỗi khung hình.
   - `visible_count(frame_h)`, `scroll(delta, frame_h)` đổi sang tính theo CHIỀU CAO
     (trước là chiều rộng).
   - **`move_selection(delta, frame_h)`** (mới) — phím lên/xuống: đổi thẳng
     `selected_index` (khác `scroll()` chỉ đổi khung nhìn) và TỰ ĐỘNG kéo `scroll_offset`
     theo nếu ô mới chọn bị khuất, đảm bảo ô đang chọn luôn nằm trong vùng nhìn thấy.
   - `draw()` vẽ cột sát cạnh phải (`frame_w - COLUMN_WIDTH` đến `frame_w`), mũi tên
     `^`/`v` (chữ, không phải hình tam giác vẽ tay — đơn giản hơn, đủ rõ) báo còn mẫu phía
     trên/dưới vùng hiện.
2. **`_decode_wheel_delta(flags)`** (mới) — tự giải mã hướng lăn chuột (xem phần tra cứu
   ở trên), có comment rõ ràng về mức độ chắc chắn và cách kiểm chứng.
3. **`_picker_mouse_callback`** cập nhật — nhận thêm `EVENT_MOUSEWHEEL`, cuộn cột theo
   hướng lăn (không đổi mẫu đang chọn, giống lăn chuột 1 trang web bình thường).
4. **`main()`**:
   - Đổi `cv2.waitKey` → `cv2.waitKeyEx` để lấy được mã phím ĐẦY ĐỦ của mũi tên (các phím
     ASCII cũ vẫn lấy đúng qua `& 0xFF` như trước, không đổi hành vi).
   - Thêm xử lý phím mũi tên lên/xuống HOẶC `w`/`s` → `picker.move_selection`.
   - Bỏ `,`/`.` (không còn hợp lý với cột dọc), đổi `s` (in calibration) → `p`.
   - `frame_size_holder` (dict chia sẻ) truyền chiều cao khung hình hiện tại cho callback
     chuột — vì callback không tự đọc được biến `frame` của vòng lặp chính.
   - Bỏ `bottom_margin` ở `draw_calibration_hint`/vị trí HUD dưới-trái (không còn cần vì
     cột kính đã chuyển sang bên phải, góc dưới-trái trống trở lại).
5. Cập nhật docstring đầu file + `window_name` cho khớp phím tắt mới.

**Về "vùng debug/ROI khung vàng"** nhắc trong mục 22: đã rà lại toàn bộ code hiện tại,
KHÔNG thấy có phần nào vẽ khung vàng/ROI debug ở bên phải màn hình (khả năng người dùng
nhớ nhầm từ 1 công cụ/bản demo khác, hoặc đây là ghi chú phòng xa cho tương lai). Cột
kính hiện đặt sát cạnh phải với `COLUMN_WIDTH=140` — nếu sau này có thêm vùng debug thật
sự đè lên, báo lại để chỉnh.

### Đã tự kiểm tra kỹ (không cần webcam)

- `py_compile` sạch.
- Test bằng khung hình giả lập: cột dọc hiện đúng 2 mẫu, thumbnail không còn bị méo/quá
  khổ (khác bản dải ngang cũ dùng lại kích thước không hợp bố cục mới).
- Giả lập 12 mẫu để ép cuộn: hiện đúng 6 ô vừa khung cao 600px, mũi tên `v` xuất hiện
  đúng lúc; lăn chuột (mô phỏng gọi `scroll()` trực tiếp) cuộn đúng 1 nấc.
- `move_selection`: di chuyển xuống 9 lần từ mẫu giả lập 12 mẫu → tự cuộn theo, ô đang
  chọn LUÔN nằm trong vùng hiển thị (assert PASS); di chuyển ngược lại về đúng đầu danh
  sách (assert PASS).
- Click chuột đúng toạ độ ô thứ 2 trong cột → chọn đúng mẫu đó (assert PASS); click ra
  ngoài cột (vùng webcam) → không đổi lựa chọn (assert PASS).
- **`_decode_wheel_delta`**: tự dựng `flags` giả lập ĐÚNG quy ước đóng gói Win32 (16 bit
  cao chứa delta có dấu, ví dụ +120/-120) rồi gọi hàm — ra đúng +120/-120 (assert PASS).
  Đây là kiểm chứng CÔNG THỨC giải mã, KHÔNG phải kiểm chứng sự kiện chuột thật (không
  làm được trong môi trường không có chuột) — xem mục "Chưa thể tự kiểm tra".
- 0 mẫu: `move_selection`/`scroll`/`handle_mouse_click` đều không crash.
- Ghép chung 1 khung: kính đeo mặt + toàn bộ HUD (tên mẫu, calibration) dồn về góc
  dưới-trái + cột kính bên phải — xem ảnh xác nhận không còn dòng nào bị dải ngang cũ che
  (giờ cột đã chuyển hẳn sang phải).
- Chạy `main()` đầy đủ tới bước mở webcam (`--camera-index 99`) + `--help` — không
  exception, mô tả tham số cập nhật đúng.

### Điều CHƯA thể tự kiểm tra (thành thật, như mục 22 đã lường trước)

- **Lăn chuột thật**: chỉ kiểm chứng được CÔNG THỨC giải mã bằng flags tự dựng, chưa thể
  xác nhận sự kiện `EVENT_MOUSEWHEEL` thật từ chuột vật lý có đến đúng như mô tả không.
- **Mã phím mũi tên qua `waitKeyEx` trên máy người dùng**: dùng giá trị phổ biến được
  nhiều nguồn độc lập xác nhận nhưng chưa tự bấm thử được. Nếu mũi tên không hoạt động,
  `w`/`s` (đã chắc chắn dùng được) là phương án thay thế ngay, không cần sửa code — chỉ
  cần dùng phím đó thay vì mũi tên.
- FPS thực tế với cột dọc (tương tự mục 21, chỉ là copy mảng + vài hình vẽ đơn giản mỗi
  khung hình, tin là không đáng kể nhưng chưa đo được số thật).

### Việc CHƯA làm — cần người dùng tự test webcam thật

DỪNG ở đây theo đúng yêu cầu mục 22:

```powershell
.\.venv\Scripts\python.exe prototype\tryon_demo.py
```

Cần xác nhận: (1) cột kính có đúng nằm sát cạnh phải, không đè lên vùng nào khác (đặc
biệt báo lại nếu thực sự có 1 khung vàng debug tôi chưa thấy trong code); (2) lăn chuột
lên/xuống có cuộn đúng chiều không (lăn xuống → thấy mẫu ở dưới, lăn lên → thấy mẫu ở
trên); (3) phím mũi tên lên/xuống có hoạt động không — nếu KHÔNG, thử `w`/`s` xem có thay
thế được không, báo lại kết quả; (4) ô đang chọn có luôn tự cuộn để hiện trong vùng nhìn
thấy khi dùng phím lên/xuống không; (5) FPS có tụt rõ so với trước không.

Cột dọc cuộn được này khi lên web sẽ thành gallery dọc có thanh cuộn (overflow-y scroll) cạnh khung camera — hành vi cuộn là mặc định của trình duyệt, không phải tự code


### 24. PROMPT — Tích hợp "Thử Kính Ảo" vào trang sản phẩm Django (chạy LOCAL)
0. ĐỌC TRƯỚC — không khảo sát lại từ đầu
Đọc CLAUDE_PROGRESS.md đầu tiên để nắm toàn bộ tiến độ, các quyết định đã chốt và cấu trúc codebase. KHÔNG khảo sát lại những gì file đó đã ghi rõ.
Prototype đã xong và chạy được ở prototype/tryon_demo.py, gồm 4 class: LightNormalizer (CLAHE trên kênh L/LAB), FaceMeshDetector (bọc FaceLandmarker Tasks API, RunningMode.VIDEO, dùng landmark 33 & 263 để suy vị trí/kích thước/góc nghiêng roll), GlassesOverlay (dán kính + xoay bằng warpAffine, alpha-blend NumPy), FPSMeter. Pipeline này đã đo ~27 FPS chạy local. TÁI SỬ DỤNG logic này, KHÔNG viết lại từ đầu.
Model MediaPipe đã tải sẵn: prototype/models/face_landmarker.task (~3.6MB).
Ảnh kính PNG nền trong suốt mẫu đã có: media/tryon/glasses/kinh.png (kính vuông đen, chụp thẳng, đối xứng qua tâm).
1. Mục tiêu phiên này

Tích hợp chức năng thử kính ảo vào web Django, chạy trên localhost.

Cụ thể: trên trang chi tiết sản phẩm (templates/products/detail.html), thêm nút/chữ "Thử kính ảo". Người dùng bấm vào → mở giao diện webcam (popup hoặc khu vực riêng ngay trong trang) → xin quyền camera → cho người dùng thấy mình đang đeo kính theo thời gian thực và chọn được các mẫu kính khác nhau từ một danh sách bên cạnh.

Đây là GIAI ĐOẠN 5 (tích hợp Django) theo tài liệu gốc. Phạm vi phiên này CHỈ là làm cho luồng cơ bản chạy được end-to-end trên local. CHƯA cần tối ưu độ trễ (Giai đoạn 3) hay xử lý outlier nâng cao — nghiêng mặt 3/4, khẩu trang... (Giai đoạn 4). Những phần đó sẽ layer thêm sau, nhưng hãy viết code có chỗ để gắn vào sau này (ví dụ tách rõ bước detect / bước vẽ).

2. Ràng buộc BẮT BUỘC (đã chốt ở CLAUDE_PROGRESS.md mục 2 — KHÔNG hỏi lại, KHÔNG đổi)
Xử lý ảnh ở server (Python/Django backend), KHÔNG xử lý client-side JS thuần. Lý do: đề cương yêu cầu OpenCV+MediaPipe và xử lý client-side sẽ triệt tiêu "Bài toán A" (độ trễ mạng cần giải quyết).
Transport: WebSocket qua Django Channels, KHÔNG dùng HTTP polling lặp lại mỗi frame. Dùng InMemoryChannelLayer (đủ cho 1 tiến trình demo local, KHÔNG cần Redis).
Tạo app mới tryon, model mới GlassesOverlay (OneToOne → products.Product) lưu file PNG kính + các số canh chỉnh. KHÔNG sửa model ProductImage hiện có; KHÔNG đụng vào các app đang chạy ổn định (accounts, products, cart, wallet, favorites).
KHÔNG dùng Bootstrap / jQuery / framework ngoài. UI viết bằng **CSS thuần
vanilla JS** đúng theo style hiện có (static/css/style.css, static/js/main.js). Không thêm CDN.
MediaPipe: dùng Tasks API (FaceLandmarker) như prototype, KHÔNG dùng mp.solutions.face_mesh (API cũ đã bị gỡ khỏi bản mediapipe đang cài).
3. Điểm riêng của chạy LOCAL (đọc kỹ để khỏi làm dư)
Chạy ở http://localhost:8000 (hoặc 127.0.0.1). Trình duyệt coi localhost là secure context nên getUserMedia() chạy được mà KHÔNG cần HTTPS. → KHÔNG tự dựng chứng chỉ tự ký / HTTPS cho phiên local này.
Máy Windows, PowerShell là shell chính. Lệnh python trần bị chặn (App Execution Alias) — gọi trực tiếp .\.venv\Scripts\python.exe.
Đường dẫn project đã thuần ASCII — KHÔNG cần workaround Unicode của MediaPipe.
Chạy được Channels ở dev bằng cách đặt daphne gần đầu INSTALLED_APPS để runserver tự chạy qua Daphne (hỗ trợ WebSocket ở dev). Nêu rõ lệnh chạy chính xác trong phần kết.

---

## 25. NHẬT KÝ PHIÊN LÀM VIỆC — hoàn thành BƯỚC A của mục 24 (hạ tầng Django: app tryon, model, Channels/ASGI)

Người dùng gõ lại yêu cầu bằng lời riêng (nút "Thử kính ảo" bấm vào mở webcam) — khớp đúng mục 24 đã soạn sẵn từ phiên trước, chưa làm gì. Đã đọc lại toàn bộ mục 1-24 trước khi code (không khảo sát lại). Xác nhận trạng thái trước khi bắt đầu: `prototype/tryon_demo.py` đúng bằng bản cuối mục 19 (UNDO về Bước A, chưa có ảnh 3/4/multi-view); `media/tryon/glasses/` chỉ có 2 ảnh thật (`Jasmin 01(BL)_f.png`, `Vanta 02_f.png` — KHÔNG còn `kinh.png` như mục 24 viết, đã tự điều chỉnh theo dữ liệu thật thay vì file không còn tồn tại); venv đã có sẵn `opencv-python`/`mediapipe` từ trước.

### Đã làm

1. Cài `channels==4.3.2`, `daphne==4.2.3` vào venv (`pip install channels daphne`).
2. Tạo app `tryon` (`manage.py startapp tryon`).
3. `core/settings.py`: thêm `"daphne"` làm phần tử ĐẦU TIÊN của `INSTALLED_APPS` (bắt buộc theo tài liệu Channels để `runserver` tự chạy qua Daphne, hỗ trợ WebSocket ở dev mà không cần đổi lệnh chạy), thêm `"channels"` và `"tryon"`. Thêm `ASGI_APPLICATION = "core.asgi.application"` và `CHANNEL_LAYERS` dùng `InMemoryChannelLayer` (đủ cho 1 tiến trình dev, không cần Redis — đúng quyết định đã chốt ở mục 24).
4. Viết lại `core/asgi.py`: dùng `ProtocolTypeRouter` (đã introspect `channels.routing` trước khi dùng, xác nhận đúng tên `ProtocolTypeRouter`/`URLRouter`, không đoán) định tuyến `http` → `get_asgi_application()` gốc (không đổi hành vi các app cũ), `websocket` → `URLRouter(tryon.routing.websocket_urlpatterns)`.
5. Tạo `tryon/routing.py` với `websocket_urlpatterns = []` — CỐ Ý để trống, vì Bước A theo đúng mục 24 chỉ là hạ tầng, consumer xử lý ảnh thật thuộc Bước B.
6. `tryon/models.py`: model `GlassesOverlay` — `product` (`OneToOneField` → `products.Product`, `related_name="glasses_overlay"`), `image` (`ImageField`, `upload_to="tryon/glasses/"`), `width_ratio`/`vertical_offset` (`FloatField`, mặc định 1.6/0.0 — chỉ dùng cho chế độ dự phòng của `GlassesOverlay` bên prototype khi không tự tìm được tâm 2 tròng kính). Đăng ký `tryon/admin.py` (`autocomplete_fields = ("product",)`, dùng được vì `ProductAdmin` đã có `search_fields`).
7. `makemigrations tryon` → `0001_initial.py`. Viết thêm `0002_seed_sample_glasses.py` (data migration, tra sản phẩm theo SLUG bằng `RunPython`, không hard-code ID) — seed 2 bản ghi mẫu: `incantation-black` ↔ `Jasmin 01(BL)_f.png`, `mythic-gold-blue-light-lens` ↔ `Vanta 02_f.png`. Sản phẩm `impossible-tokyo-tort` CỐ Ý chưa có ảnh AR (chỉ có 2 ảnh PNG thật, chưa có ảnh thứ 3) — trang chi tiết của nó sẽ ẩn nút "Thử kính ảo" ở Bước C cho tới khi có ảnh mới, không phải lỗi.
8. Cập nhật `requirements.txt`: thêm `channels==4.3.2`, `daphne==4.2.3`, `opencv-python==5.0.0.93`, `mediapipe==0.10.35` (đúng bản đã cài, không đoán).
9. Tạo `.gitignore` mới (repo trước đó chưa có file này): `.env`, `.venv/`, `__pycache__/`/`*.pyc`, `staticfiles/`, `db.sqlite3`, và `prototype/models/*.task` (file nhị phân ~3.6MB tải từ Google, không phải source code tự viết — URL tải lại đã ghi ở mục 4).

### Đã tự kiểm tra

- MySQL (XAMPP) ban đầu chưa chạy — đã hỏi và người dùng tự bật qua XAMPP Control Panel trước khi tiếp tục `migrate`.
- `manage.py check` sạch (0 lỗi) cả trước và sau khi có DB.
- `manage.py makemigrations --check --dry-run` → "No changes detected" (model và migration khớp nhau).
- `manage.py migrate` chạy sạch, `showmigrations tryon` xác nhận cả `0001_initial` và `0002_seed_sample_glasses` đã áp dụng.
- Xác nhận qua shell: 2 bản ghi `GlassesOverlay` seed đúng sản phẩm, `image.storage.exists(...)` trả `True` cho cả 2 (file ảnh thật sự tồn tại trên đĩa, không phải đường dẫn ảo).
- Bật thử server, `curl` các route cũ (`/`, `/san-pham/incantation-black/`, `/san-pham/mythic-gold-blue-light-lens/`, `/admin/login/`) đều trả `200` — app cũ không bị phá.

### Lưu ý quan trọng cho phiên/lần chạy sau

Phát hiện trong lúc test: cổng 8000 đang bị một tiến trình `manage.py runserver` (venv, KHÔNG mang tham số cổng, PID lúc phát hiện là 91212, cây tiến trình gốc PID 94764) **có sẵn từ trước phiên này** chiếm giữ — không phải do phiên này khởi động. Đã dừng đúng tiến trình runserver LỖI do chính tôi tự bật thử (không bind được cổng vì lý do trên), KHÔNG đụng vào tiến trình có sẵn đó vì không chắc đó có phải cửa sổ người dùng đang tự dùng hay không. **Người dùng nên tự kiểm tra/đóng cửa sổ terminal đang chạy `runserver` cũ đó trước khi tự chạy lại**, để đảm bảo server mới khởi động sẽ nạp đúng cấu hình Channels/Daphne vừa thêm (tiến trình cũ khởi động TRƯỚC khi có `daphne`/`channels` trong `INSTALLED_APPS` — dù Django tự động reload khi sửa file, chưa kiểm chứng chắc chắn được liệu nó đã chuyển hẳn sang chạy qua Daphne hay chưa).

### Việc CHƯA làm — chờ người dùng duyệt trước khi sang Bước B

Theo đúng mục 24, DỪNG ở đây. Bước A chỉ là hạ tầng (chưa có consumer xử lý ảnh thật, chưa có UI) — cần người dùng xác nhận đã đọc phần "đã thêm" ở trên và đồng ý là chưa phá gì trước khi sang **BƯỚC B — WebSocket Consumer** (chuyển 4 class từ `prototype/tryon_demo.py` vào `tryon/vision.py`, viết `AsyncWebsocketConsumer` nhận/xử lý/trả khung hình).

---

## 26. NHẬT KÝ PHIÊN LÀM VIỆC — hoàn thành BƯỚC B + BƯỚC C của mục 24 (consumer thật + giao diện)

Người dùng bối rối vì Bước A không có gì để xem trên web (đúng - đó chỉ là hạ tầng), nên đã đồng ý làm liền BƯỚC B + BƯỚC C trong cùng 1 phiên thay vì dừng giữa chừng thêm 1 lần nữa, chỉ dừng lại DUY NHẤT ở cuối để test webcam thật.

### BƯỚC B — `tryon/vision.py` + `tryon/consumers.py` + `tryon/routing.py`

- **`tryon/vision.py`**: port gần như nguyên vẹn 3 class từ `prototype/tryon_demo.py` (đúng bản mục 19 - "Bước A", KHÔNG kèm ảnh 3/4/GlassesPicker): `LightNormalizer`, `FaceMeshDetector`, `GlassesOverlay` (auto-align 2 điểm neo tâm tròng + fallback `width_ratio`/`vertical_offset`). KHÔNG port `GlassesPicker`/`FPSMeter`/`main()` — đó là giao diện cửa sổ OpenCV riêng cho prototype, không dùng được trên web (gallery web dùng HTML/JS thay thế ở Bước C).
- **`tryon/consumers.py`**: `TryOnConsumer(AsyncWebsocketConsumer)`. Đã tự thiết kế giao thức (ghi rõ trong docstring vì đây là thiết kế riêng, không phải chuẩn có sẵn — tránh người đọc sau nhầm là đang theo 1 chuẩn nào đó):
  - Client → server: tin nhắn VĂN BẢN (JSON) `{"action":"select_glasses","glasses_id":N}` / `{"action":"calibrate","width_ratio":X,"vertical_offset":Y}`; tin nhắn NHỊ PHÂN = 1 khung hình JPEG.
  - Server → client: LUÔN 1 tin nhắn NHỊ PHÂN DUY NHẤT cho mỗi khung hình nhận được — byte đầu tiên là cờ trạng thái (1 = có mặt, 0 = không), phần còn lại là JPEG đã xử lý (gộp 2 thứ vào 1 tin nhắn thay vì tách JSON + binary riêng để không phụ thuộc giả định "thứ tự tin nhắn" mong manh phía client).
  - Mỗi kết nối tạo **riêng** 1 `FaceMeshDetector` (đúng yêu cầu mục 24 — chế độ VIDEO cần trạng thái bám vết + timestamp riêng từng client), đóng khi `disconnect()`.
  - Toàn bộ code CPU-bound (decode/CLAHE/MediaPipe/blend/encode) được đẩy qua `sync_to_async(..., thread_sensitive=False)` để không chặn event loop; truy vấn DB dùng `database_sync_to_async` (đã introspect API `channels.generic.websocket`/`channels.db`/`asgiref.sync` trước khi dùng, không đoán).
  - **Tự phát hiện + sửa 1 lỗi khi rà soát**: dòng `cv2.flip(frame, 1)` (lật ngang cho giống soi gương) nằm trong `main()` của prototype (không nằm trong 3 class), nên bị sót khi port ban đầu — đã bổ sung lại vào `_process_frame_sync`.
- **`tryon/routing.py`**: 1 route `ws/tryon/` → `TryOnConsumer` (route CHUNG cho mọi sản phẩm — client tự gửi `select_glasses` sau khi kết nối để chọn đúng mẫu kính của trang đang xem, không cần route riêng từng sản phẩm).

### BƯỚC C — Giao diện

- **`products/views.py`**: view `detail` thêm `product_glasses_overlay` (dùng try/except `GlassesOverlay.DoesNotExist` vì quan hệ OneToOne "ngược" không tự trả `None`) và `tryon_gallery` (toàn bộ `GlassesOverlay` hiện có, không chỉ của sản phẩm đang xem — cho phép so sánh nhiều mẫu ngay trên 1 trang, giống `GlassesPicker` ở prototype).
- **`templates/products/detail.html`**: nút "Thử kính ảo" (chỉ hiện nếu `product_glasses_overlay` tồn tại — sản phẩm "Impossible" chưa có ảnh AR nên KHÔNG hiện nút, đã xác nhận bằng curl) mở modal gồm khung `<video>`/`<img>` hiển thị kết quả, 2 thanh trượt hiệu chỉnh (chỉ có tác dụng ở chế độ dự phòng), và gallery các mẫu kính (thumbnail cuộn dọc, bấm đổi kính ngay — tương đương `GlassesPicker` nhưng bằng HTML/JS như đã ghi chú ở mục 20).
- **`static/js/tryon.js`** (file mới, KHÔNG gộp vào `main.js` vì phạm vi/độ phức tạp riêng — chỉ nạp khi trang có nút thử kính): `getUserMedia()` xin quyền camera → vòng lặp chụp khung mỗi ~80ms vào canvas ẩn → nén JPEG → gửi qua WebSocket **chỉ khi khung trước đã có phản hồi** (biến `waitingForResponse`, đúng yêu cầu "tránh dồn ứ" mục 24) → nhận khung nhị phân, tách byte cờ trạng thái + JPEG, hiển thị qua `Blob`/`URL.createObjectURL` (thu hồi URL cũ mỗi lần để không rò rỉ bộ nhớ). Đóng modal → đóng WebSocket + `stream.getTracks().forEach(t => t.stop())` (tắt đèn camera thật). Bấm mẫu kính trong gallery hoặc kéo 2 thanh trượt → gửi lệnh tương ứng qua WebSocket ngay lập tức.
- **`static/css/style.css`**: thêm section mới (theo đúng quy ước CSS thuần hiện có, dùng lại biến `--color-*`/`--radius-*`/`--shadow-*`) cho modal + gallery + thanh trượt.
- **Tự phát hiện + sửa 1 lỗi khi rà soát**: locale `"vi"` đặt `DECIMAL_SEPARATOR = ","` (`core/formats/vi/formats.py`, có từ trước) khiến Django tự render `{{ width_ratio }}` thành `"1,6"` — **không hợp lệ** cho `<input type="range" value="...">` (HTML luôn cần dấu CHẤM bất kể locale, trình duyệt sẽ bỏ qua giá trị). Đã bọc 2 input này bằng `{% localize off %}` và xác nhận lại bằng curl: `value="1.6"`/`value="0.0"` đúng.

### Đã tự kiểm tra (không cần webcam thật)

- `manage.py check` + `makemigrations --check --dry-run` sạch.
- **Test consumer bằng `channels.testing.WebsocketCommunicator`** (script tạm, đã xoá): kết nối OK, chọn mẫu kính OK, gửi 1 khung JPEG giả (ảnh xám, không có mặt thật) → nhận đúng định dạng phản hồi (byte cờ + JPEG đọc lại được, đúng kích thước), gửi id kính không tồn tại → nhận đúng lỗi JSON, gửi JSON hỏng → nhận đúng lỗi JSON và consumer không crash, `disconnect()` sạch.
- **Test riêng `tryon/vision.py` bằng điểm mắt giả lập** (không qua MediaPipe, giống cách làm ở mục 14): dán cả 2 ảnh PNG thật (`Jasmin 01(BL)`, `Vanta 02`) lên nền da giả — xem ảnh xuất ra xác nhận bằng mắt: tâm tròng kính khớp đúng 2 điểm neo, không có viền màu lạ, xoay đúng khi giả lập nghiêng đầu — khớp hành vi đã kiểm chứng ở prototype, không hồi quy khi port.
- **Test WebSocket THẬT qua mạng** (cài tạm gói `websockets`, test xong gỡ ra khỏi venv để không lệch với `requirements.txt`): kết nối thật tới server dev đang chạy qua `ws://127.0.0.1:8000/ws/tryon/`, gửi khung giả, nhận đúng phản hồi — xác nhận `core/asgi.py`/`tryon/routing.py`/Daphne hoạt động đúng, không chỉ đúng ở tầng consumer đơn lẻ.
- Curl xác nhận: nút/modal chỉ xuất hiện ở sản phẩm CÓ ảnh AR (Incantation, Mythic), KHÔNG xuất hiện ở sản phẩm chưa có (Impossible); `static/js/tryon.js` phục vụ được (200); trang chủ/trang sản phẩm/`/admin/` vẫn 200 bình thường.

### Điều CHƯA thể tự kiểm tra (thành thật) — cần người dùng tự test webcam thật

Claude Code không có webcam/trình duyệt thật ở môi trường này, nên CHƯA xác nhận được:
- Đường "CÓ phát hiện khuôn mặt" chạy qua đúng luồng web thật (webcam trình duyệt → JS → WebSocket → MediaPipe) — mọi test tự động ở trên chỉ dùng ảnh giả không có mặt thật hoặc điểm mắt giả lập tay, CHƯA chạy qua MediaPipe với khuôn mặt thật trên đường WebSocket.
- Kính có dán đúng vị trí/góc xoay trên khuôn mặt thật khi xem qua trình duyệt (thuật toán đã được xác nhận ở prototype/webcam trực tiếp mục 14/19, nhưng đường đi qua nén JPEG hai lượt + WebSocket + trình duyệt là mới, chưa tự kiểm chứng bằng mắt thật).
- Hướng soi gương (lật ngang) có đúng cảm giác tự nhiên không.
- Bấm đổi mẫu kính trong gallery, kéo 2 thanh trượt có phản hồi đúng trên khuôn mặt thật không.
- Đóng khu vực thử kính có tắt đèn camera thật không (logic `stream.getTracks().forEach(t => t.stop())` đã viết đúng theo tài liệu chuẩn nhưng chưa tự bấm thử).
- Độ trễ/độ mượt cảm nhận được (CHƯA tối ưu gì - đúng phạm vi đã chốt, việc đo/tối ưu thuộc Giai đoạn 3 riêng, chưa làm trong phiên này).

### Cách chạy để test

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Mở `http://127.0.0.1:8000/san-pham/incantation-black/` (hoặc `mythic-gold-blue-light-lens`), bấm "Thử kính ảo" → "Bật camera" → cho phép quyền camera. Kiểm tra đúng theo tiêu chí nghiệm thu mục 24 phần 6.

---

## 27. NHẬT KÝ PHIÊN LÀM VIỆC — sửa 2 lỗi người dùng báo sau khi tự test (CSS modal luôn hiện + vị trí nút)

Người dùng tự mở trang test, báo "nút không hoạt động và css lỗi", yêu cầu nút phải nằm bên cạnh ảnh sản phẩm. Đã đọc lại code (không đoán) để xác định đúng nguyên nhân gốc trước khi sửa.

### Lỗi 1 — Modal luôn hiển thị sẵn (nguyên nhân "css lỗi" + "nút không hoạt động")

**Nguyên nhân gốc**: CSS `.tryon-modal { position:fixed; inset:0; z-index:1000; display:flex; ... }` đặt `display:flex` KHÔNG ĐIỀU KIỆN. Thuộc tính HTML `hidden` (JS dùng `modal.hidden = true/false` để ẩn/hiện) chỉ hoạt động nhờ rule mặc định của trình duyệt `[hidden]{display:none}` nằm trong **UA stylesheet** — mà CSS của **author** (file `style.css` của chính dự án) LUÔN thắng UA stylesheet ở cùng mức độ quan trọng, BẤT KỂ độ đặc tả (specificity) so sánh thế nào. Kết quả: modal **hiện sẵn toàn màn hình ngay từ lúc tải trang** (nền đen mờ che hết giao diện = "css lỗi"), và bấm nút "Thử kính ảo" không thấy gì đổi vì modal vốn đã ở trạng thái "mở" liên tục = "nút không hoạt động".

**Đã sửa**: thêm rule `.tryon-modal[hidden] { display: none; }` ngay sau rule cũ — selector này có độ đặc tả CAO HƠN `.tryon-modal` (thêm 1 attribute selector) nên thắng được rule `display:flex`, khiến `hidden` hoạt động đúng trở lại. Đã xác nhận bằng curl: HTML vẫn render đúng `id="tryon-modal" hidden`.

### Lỗi 2 — Vị trí nút (yêu cầu mới, không phải lỗi code)

Nút "Thử kính ảo" trước đặt trong cột `.product-info` (cạnh nút "Thêm vào giỏ hàng") — người dùng muốn nó nằm bên cạnh ảnh sản phẩm. Đã chuyển nút vào bên trong `.product-gallery-main` (cùng khối với ảnh chính), hiển thị dạng nút nổi (overlay) ở góc dưới-phải của ảnh — mẫu phổ biến trên các trang bán kính có AR. Thêm `position: relative` cho `.product-gallery-main` (để định vị `position: absolute` cho nút) và class `.tryon-gallery-trigger` mới trong `style.css`.

### Đã tự kiểm tra

- `manage.py check` sạch.
- Curl xác nhận: nút chỉ xuất hiện ĐÚNG 1 lần, nằm bên trong `product-gallery-main` (cạnh `<img data-gallery-main>`), không còn ở cột thông tin nữa.
- Curl xác nhận `#tryon-modal` vẫn có thuộc tính `hidden` khi tải trang (đúng trạng thái đóng mặc định).
- Rà lại toàn bộ file `style.css`, xác nhận không còn rule nào khác đặt `display` cho `.tryon-modal` gây xung đột.

### Việc CHƯA thể tự kiểm tra

Vẫn cần người dùng tự mở trình duyệt xác nhận: modal giờ đã ẩn đúng lúc tải trang, bấm nút mở/đóng mượt, vị trí nút nổi trên ảnh có che mất chi tiết ảnh quan trọng không (nếu cần dịch chuyển góc khác, báo lại).
4. Việc cần làm — chia thành 3 bước, DỪNG xin duyệt sau mỗi bước
BƯỚC A — Hạ tầng backend (chưa có UI)
Tạo app tryon (thêm vào INSTALLED_APPS).
Model GlassesOverlay: product (OneToOne → products.Product), image (ImageField, upload_to="tryon/glasses/", PNG nền trong suốt), và 2 số canh chỉnh width_ratio (float, độ rộng kính so với khoảng cách 2 khoé mắt) và vertical_offset (float, dịch dọc). Migrate.
Seed 1 bản ghi mẫu trỏ tới media/tryon/glasses/kinh.png (gắn vào một Product có sẵn để test). Có thể để width_ratio/vertical_offset mặc định hợp lý, người dùng sẽ canh lại bằng UI ở Bước C.
Thêm channels + daphne vào INSTALLED_APPS và requirements.txt; cấu hình ASGI_APPLICATION, CHANNEL_LAYERS = {InMemoryChannelLayer}, viết lại core/asgi.py để định tuyến cả HTTP lẫn WebSocket (ProtocolTypeRouter).
Tạo .gitignore mới nếu chưa có (ít nhất: .env, __pycache__/, *.pyc, staticfiles/, .venv/, và cân nhắc file .task nếu không muốn commit binary).
DỪNG: giải thích những gì đã thêm, xác nhận migrate sạch, chưa phá gì.
BƯỚC B — WebSocket Consumer (bộ não xử lý)
Chuyển logic 4 class từ prototype/tryon_demo.py vào trong app tryon (ví dụ tryon/vision.py), giữ nguyên thuật toán, chỉ bỏ phần OpenCV window / phím / chuột (không dùng trên web).
Điểm khác prototype: GlassesOverlay giờ dán PNG kính thật (từ model) thay vì vẽ kính demo bằng ellipse. Dùng width_ratio/vertical_offset từ model để canh. Vẫn resize + xoay theo góc roll + alpha-blend như prototype.
Viết AsyncWebsocketConsumer: nhận khung hình (binary hoặc base64 JPEG từ client) → decode (cv2.imdecode) → chạy pipeline → trả kết quả về client.
MediaPipe/OpenCV là code đồng bộ nặng → đẩy qua thread (sync_to_async hoặc run_in_executor) để KHÔNG chặn event loop.
Mỗi kết nối có 1 instance FaceLandmarker riêng (VIDEO mode cần trạng thái + timestamp tăng đơn điệu riêng cho từng client).
Xử lý tin nhắn "đổi kính" (client gửi id/slug mẫu kính) → các khung sau dùng PNG mới.
Không có mặt trong khung → trả khung gốc + cờ báo "không thấy mặt" (client hiện gợi ý tiếng Việt). Tránh chia cho 0 khi 2 landmark trùng nhau.
DỪNG: giải thích luồng, tự test phần có thể test (xem mục 5), báo rõ phần cần webcam thật.
BƯỚC C — Giao diện (frontend)
Trong templates/products/detail.html: thêm nút/chữ "Thử kính ảo". Bấm → mở khu vực try-on (modal hoặc block hiện ra), gồm:
Thẻ <video> (stream webcam) + <canvas> (nơi vẽ khung đã xử lý nhận từ server) — hoặc <img> hiển thị khung server trả về.
Gallery kính bên cạnh: danh sách HTML cuộn được (overflow-y: scroll), mỗi mẫu là 1 thumbnail bấm chọn được (thay cho cột kính OpenCV ở prototype).
2 thanh trượt/ô nhập cho width_ratio và vertical_offset để người dùng canh trực quan; giá trị gửi lên server qua WebSocket (không cần lưu DB ở phiên này, chỉ cần canh xong đọc ra 2 số để nhập vào model sau).
JS (vanilla) lo: getUserMedia() xin camera → vòng lặp ~10–15 lần/giây chụp khung từ <video> vào canvas ẩn → nén JPEG → gửi qua WebSocket → nhận khung đã xử lý → hiển thị. Chỉ gửi khung mới khi khung trước đã xử lý xong (tránh dồn ứ). Đóng try-on → đóng WebSocket + stream.getTracks().forEach(t => t.stop()) để tắt đèn camera.
Xử lý lỗi phía client: người dùng từ chối quyền / không có camera → hiện thông báo tiếng Việt, không để trắng màn hình.
Style theo static/css/style.css hiện có, không thêm thư viện.
DỪNG: hướng dẫn người dùng tự chạy webcam thật để kiểm tra trực quan.
5. Cách làm việc (đúng tinh thần các phiên trước)
Giải thích trước khi code, ưu tiên giải pháp đơn giản hơn giải pháp phức tạp. Comment tiếng Việt giải thích tại sao, không chỉ mô tả cái gì.
KHÔNG đoán API — introspect/tra tài liệu thật trước khi dùng (Channels, cách chạy sync code trong async, chữ ký hàm...).
Nói thẳng nếu thấy chỗ nào sai kỹ thuật thay vì làm theo mù quáng.
Trung thực về giới hạn môi trường: Claude Code KHÔNG có webcam thật ở đây. Hãy tự kiểm tra những gì kiểm tra được (import sạch, py_compile, migrate chạy, consumer xử lý đúng với 1 khung hình giả lập dựng bằng NumPy/ảnh tĩnh, decode/encode JPEG hai chiều đúng), và đánh dấu RÕ phần nào bắt buộc người dùng phải tự chạy webcam thật mới xác nhận được (bám vị trí, góc xoay, FPS thực end-to-end).
Cập nhật CLAUDE_PROGRESS.md sau khi xong (thêm mục nhật ký phiên).
6. Tiêu chí nghiệm thu (người dùng sẽ tự kiểm bằng webcam thật)

Chạy (nêu chính xác lệnh, ví dụ):

powershell
.\.venv\Scripts\python.exe manage.py runserver

Mở http://localhost:8000, vào 1 sản phẩm đã gắn GlassesOverlay, bấm "Thử kính ảo". Cần đạt:

Trình duyệt xin quyền camera; cho phép → thấy hình webcam của mình.
Thấy kính được dán lên mặt, cập nhật real-time, xoay theo khi nghiêng đầu.
Bấm chọn mẫu kính khác trong gallery → kính đổi theo.
Chỉnh 2 thanh trượt → vị trí/độ rộng kính thay đổi trực quan (để canh 2 số).
Đóng try-on → đèn webcam tắt (stream dừng).
Các app cũ (products, cart...) vẫn chạy bình thường, không lỗi.
---

## 28. PROMPT SỬA LỖI (sau khi người dùng test web thật) — bỏ bắt đăng nhập, bỏ 2 thanh trượt, sửa luồng camera, nút TRY ON, lỗi lộ comment

> Phần web thử kính (mục 24–27) đã chạy. Người dùng test thật, báo các lỗi dưới. Sửa
> theo NGUYÊN NHÂN GỐC, KHÔNG chắp vá; KHÔNG phá app cũ. Tự kiểm bằng curl phần render,
> rồi **DỪNG chờ người dùng test webcam thật**. Comment tiếng Việt.

### LỖI 1 — Đang bắt đăng nhập mới cho thử kính (SAI)

Thử kính ảo là chức năng của **khách vãng lai (Khách hàng tiềm năng)** — **KHÔNG cần
đăng nhập** (khớp đúng sơ đồ use case đã thiết kế). Hiện code đang chặn phải đăng nhập.

- **Tìm chỗ đang chặn** (có thể ở một trong các nơi sau, kiểm hết):
  - `@login_required` / `LoginRequiredMixin` trên view liên quan thử kính.
  - `{% if user.is_authenticated %}` bao quanh nút "Thử kính ảo" hoặc modal trong
    `templates/products/detail.html`.
  - Kiểm tra `self.scope["user"].is_authenticated` trong `tryon/consumers.py` (từ chối
    kết nối WebSocket nếu chưa đăng nhập).
  - Redirect tới trang login ở JS khi bấm nút.
- **Bỏ chặn** ở luồng thử kính. Xác nhận: **đăng xuất hoàn toàn** rồi vẫn bấm TRY ON và
  thử kính bình thường.

### LỖI 2 — Bỏ 2 thanh trượt "Bề rộng kính" / "Lệch dọc" khỏi giao diện web

Auto-fit theo 2 tâm tròng đã đủ; **không phơi chế độ chỉnh tay ra người dùng cuối**.

- Xóa 2 `<input type="range">` + nhãn của chúng khỏi modal trong `detail.html`.
- Xóa đoạn JS trong `static/js/tryon.js` gửi lệnh `calibrate` qua WebSocket (và bỏ
  listener của 2 slider).
- **Giữ** `width_ratio`/`vertical_offset` trong model + fallback phía server làm mặc
  định **IM LẶNG** (không có UI). Consumer vẫn chấp nhận nhưng client không gửi nữa.

### LỖI 3 — Ghi chú Django lộ ra màn hình ("{# localize off BAT BUOC... #}")

**Nguyên nhân gốc**: `{# ... #}` của Django là comment **MỘT DÒNG**. Ghi chú đang viết
**nhiều dòng** nên KHÔNG được coi là comment → Django render nguyên văn ra trang.

- **Sửa**: **xóa hẳn** ghi chú đó — nó chỉ giải thích cho 2 input vừa bị xóa ở Lỗi 2,
  giờ không còn cần. Đồng thời bỏ `{% localize off %}...{% endlocalize %}` nếu block đó
  chỉ tồn tại để phục vụ 2 input đã xóa.
- Quy tắc chung cho về sau: ghi chú nhiều dòng trong template phải dùng
  `{% comment %}...{% endcomment %}`, KHÔNG dùng `{# #}`.

### LỖI 4 — Luồng camera: bấm TRY ON là mở camera luôn, BỎ nút "Bật camera"

Hiện tại: TRY ON → modal hiện nút "Bật camera" + câu "Bấm nút bên dưới để bật camera…"
→ mới `getUserMedia()`. **Thừa** — cú bấm TRY ON đã là user-gesture đủ để gọi
`getUserMedia()` trực tiếp, và **trình duyệt TỰ hiện hộp xin quyền camera**.

- **Sửa**: trong handler bấm nút TRY ON (mở modal), gọi **luôn** `getUserMedia()`. **Bỏ**
  nút "Bật camera" và câu hướng dẫn "Bấm nút bên dưới…".
- **Giữ xử lý duyên dáng khi lỗi** (chỉ hiện KHI có lỗi, không phải màn hình mặc định):
  - Người dùng **từ chối quyền** / **không có camera** / trình duyệt không hỗ trợ →
    hiện thông báo tiếng Việt rõ ràng + một nút **"Thử lại"**.
- Đóng modal vẫn `stream.getTracks().forEach(t => t.stop())` để tắt đèn camera (giữ nguyên).

### VIỆC THÊM — Nút "TRY ON" theo mẫu tham khảo

Người dùng muốn nút dạng **viên thuốc "TRY ON"** (kèm icon kính nhỏ), đặt nổi ở góc
ảnh sản phẩm — như ảnh tham khảo trang bán kính. Chỉnh class `.tryon-gallery-trigger`
trong `style.css`: bo tròn (pill), chữ "TRY ON" (hoặc "Thử kính"), thêm icon kính nhỏ,
nền tương phản nhẹ. **Giữ nguyên hành vi mở modal + mở camera** (Lỗi 4).

### Tự kiểm & dừng

- Curl xác nhận: trang chi tiết render KHÔNG còn 2 input range, KHÔNG còn dòng
  `{# localize... #}`, nút TRY ON có mặt; các trang cũ vẫn 200.
- Xác nhận luồng khách vãng lai (chưa đăng nhập) vào được thử kính (test route/logic).
- **DỪNG — người dùng test webcam thật**: đăng xuất → bấm TRY ON → trình duyệt tự hỏi
  quyền → thấy kính; không còn nút "Bật camera", không còn 2 thanh trượt, không còn dòng
  chữ lạ.

---

## 29. NHẬT KÝ PHIÊN LÀM VIỆC — hoàn thành mục 28 (4 lỗi + nút TRY ON)

Đọc lại toàn bộ mục 24-28 trước khi làm (không khảo sát lại code từ đầu). Đã sửa từng
lỗi theo đúng nguyên nhân gốc, không chắp vá.

### LỖI 1 — KHÔNG tái hiện được trong code hiện tại (đã báo thẳng cho người dùng)

Đã rà **toàn bộ** đường đi của luồng thử kính trước khi sửa bất cứ gì: `products/views.py`
(view `detail`), `tryon/consumers.py` (`connect()`), `tryon/routing.py`, `core/asgi.py`
(không bọc `AuthMiddlewareStack`), `templates/products/detail.html` (nút/modal không nằm
trong `{% if user.is_authenticated %}`), `core/settings.py` (không có middleware bắt đăng
nhập toàn cục, `MIDDLEWARE` chỉ có các middleware mặc định của Django) — **không tìm thấy
bất kỳ chỗ nào chặn đăng nhập** cho thử kính. Đã tự kiểm chứng bằng 2 cách thật (không chỉ
đọc code): (a) `curl` trang chi tiết sản phẩm không kèm cookie nào → vẫn thấy nút TRY ON +
modal render bình thường; (b) viết script Python dùng `socket` thuần gửi thẳng HTTP
Upgrade request tới `/ws/tryon/` không kèm bất kỳ cookie/session nào → nhận về đúng
`HTTP/1.1 101 Switching Protocols` (kết nối được chấp nhận, không bị từ chối/redirect về
trang login). **Kết luận: không sửa gì ở mục này** vì không có gì để sửa — có thể lúc
người dùng test, trình duyệt đang giữ sẵn cookie đăng nhập từ trước nên tưởng nhầm là bị
chặn, hoặc đã nhầm với nút "Thêm vào giỏ hàng" (nút này POST tới `cart:add`, VIEW đó có
`@login_required` thật — nhưng đó là hành vi ĐÚNG và có chủ đích của giỏ hàng, không phải
của thử kính). Nếu người dùng vẫn gặp lại, cần mô tả CHÍNH XÁC bước nào bị chuyển hướng để
định vị lại.

### LỖI 2 + LỖI 3 — Bỏ 2 thanh trượt + dòng comment lộ ra màn hình

- `templates/products/detail.html`: xóa toàn bộ khối `.tryon-calibration` (2 input range +
  nhãn + đoạn comment nhiều dòng `{# ... #}` bị lộ + wrapper `{% localize off %}`). Bỏ luôn
  `l10n` khỏi `{% load %}` ở đầu file vì không còn chỗ nào dùng `{% localize %}` nữa.
- `static/js/tryon.js`: xóa biến `widthRatioInput`/`verticalOffsetInput`, 2 listener
  `"input"`, hàm `sendCalibration()` và lệnh gọi nó lúc mở socket.
- **Giữ nguyên** `width_ratio`/`vertical_offset` trên model `GlassesOverlay` và toàn bộ
  logic `_apply_calibration()`/action `"calibrate"` trong `tryon/consumers.py` — consumer
  vẫn hiểu lệnh này (không cần sửa backend), chỉ là client không còn gửi nữa, đúng yêu cầu
  "giữ làm mặc định IM LẶNG, không có UI".

### LỖI 4 — Bấm TRY ON mở camera luôn, bỏ nút "Bật camera"

- `static/js/tryon.js`: chuyển lời gọi `getUserMedia()` (nằm trong hàm `startCamera()`)
  vào thẳng handler `click` của `openBtn` (nút TRY ON) — bấm nút đã tính là 1 "user
  gesture" hợp lệ, trình duyệt tự hiện hộp thoại xin quyền camera mà không cần thêm 1 cú
  bấm trung gian.
- Đổi khối `#tryon-placeholder` trong `detail.html`: bỏ hẳn nút "Bật camera" + câu hướng
  dẫn cũ, thay bằng 1 dòng chữ trung tính "Đang mở camera…" (`#tryon-placeholder-text`,
  cập nhật được bằng JS) + 1 nút "Thử lại" (`#tryon-retry`, **mặc định `hidden`**, CHỈ hiện
  ra khi `getUserMedia()` thất bại — đúng yêu cầu "chỉ hiện KHI có lỗi, không phải màn hình
  mặc định"). Khi lỗi (từ chối quyền/không có camera/trình duyệt không hỗ trợ), hàm
  `showCameraError()` đổi chữ thành thông báo tiếng Việt cụ thể + hiện nút "Thử lại" (bấm
  vào gọi lại đúng `startCamera()`). Đóng modal (`stopTryOn()`) reset lại placeholder về
  trạng thái mặc định "Đang mở camera…" + ẩn nút "Thử lại", để lần mở tiếp theo không còn
  dính thông báo lỗi cũ.

### VIỆC THÊM — Nút TRY ON dạng viên thuốc

Phát hiện khi rà code: class `.tryon-gallery-trigger` (trong `static/css/style.css`) đã
**sẵn là hình viên thuốc bo tròn 999px, có icon kính, đặt nổi góc dưới-phải ảnh sản phẩm**
từ lần sửa Lỗi 2 ở mục 27 (đổi vị trí nút) — tức phần lớn yêu cầu này đã làm xong từ trước
khi người dùng viết mục 28. Việc còn thiếu thật sự chỉ là CHỮ trên nút: đổi từ "Thử kính
ảo" → **"TRY ON"** (đúng chữ người dùng nêu trong ảnh tham khảo), thêm `text-transform:
uppercase` + `letter-spacing` để đọc giống 1 badge/pill thật thay vì chỉ là nút bo tròn có
chữ thường.

### Dọn dẹp thêm (tự phát hiện, không phải yêu cầu gốc)

Sau khi xóa `.tryon-calibration` khỏi HTML, 3 rule CSS `.tryon-calibration`,
`.tryon-calibration label`, `.tryon-calibration input[type="range"]`, và `.tryon-hint`
trong `style.css` trở thành CSS chết (không còn phần tử HTML nào dùng tới) — đã xóa hẳn
thay vì để lại rác, đã `grep` xác nhận không còn nơi nào khác tham chiếu tới các class này
trước khi xóa.

### Đã tự kiểm tra

- `manage.py check` sạch (0 lỗi).
- `node --check static/js/tryon.js` — cú pháp JS hợp lệ.
- Bật `runserver` thật, `curl` xác nhận trên trang `incantation-black`: **0** input
  `type="range"`, **0** dòng chứa "localize off BAT BUOC" (comment lộ), **0** dòng "Bật
  camera" (nút cũ), có đúng 1 nút chữ "TRY ON", `#tryon-retry` tồn tại với thuộc tính
  `hidden`, `#tryon-placeholder-text` chứa đúng "Đang mở camera…".
- `curl` xác nhận trang `impossible-tokyo-tort` (sản phẩm CHƯA có ảnh AR) vẫn **không**
  render nút TRY ON / không nạp `tryon.js` — đúng hành vi cũ, không bị ảnh hưởng.
- `curl` toàn bộ route cũ (`/`, 3 trang chi tiết, `/admin/login/`, `static/js/tryon.js`,
  `static/css/style.css`) đều trả `200`.
- Đã dừng hẳn tiến trình `runserver` do phiên này tự bật sau khi test xong, để không lặp
  lại đúng sự cố "chiếm cổng 8000 từ phiên trước" đã ghi nhận ở mục 25.
- KHÔNG đụng tới `tryon/consumers.py`/`tryon/vision.py` (backend xử lý ảnh) trong phiên
  này — chỉ sửa template/JS/CSS, nên toàn bộ pipeline OpenCV/MediaPipe không có nguy cơ hồi
  quy từ những thay đổi này.

### Việc CHƯA thể tự kiểm tra — cần người dùng tự test webcam thật

- Bấm TRY ON có mở ngay hộp thoại xin quyền camera của trình duyệt không (không còn màn
  hình trung gian).
- Từ chối quyền / rút webcam ra thử → có hiện đúng thông báo lỗi tiếng Việt + nút "Thử
  lại", bấm "Thử lại" có xin quyền lại được không.
- Đăng xuất hẳn tài khoản rồi thử lại luồng thử kính từ đầu (để loại trừ khả năng LỖI 1
  chỉ do cookie phiên cũ như đã nêu ở trên).
- Cảm nhận trực quan nút "TRY ON" mới (chữ hoa, letter-spacing) trên ảnh sản phẩm thật.

### Cách chạy để test

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Mở `http://127.0.0.1:8000/san-pham/incantation-black/`, đăng xuất nếu đang đăng nhập, bấm
nút "TRY ON" nổi trên ảnh sản phẩm.

## 30 - bạn hãy đặt tên website đồng hồ là Cadran d'Or, thiết kế chữ hiệu ứng gradien đậm nhạt dần từ trên xuống dưới 
- khi chọn kính ở web cam thì khung hình trở nên tối hơn hãy tăng độ sáng, vì khung hình quá tối khi chọn kính
-

---

## 30. PROMPT — Đánh giá sản phẩm kiểu Shopee (đăng nhập + ĐÃ MUA mới đánh giá) + cảm xúc + seed dữ liệu

> Xây tính năng đánh giá sản phẩm đúng logic Shopee: chỉ người **đã đăng nhập** và **đã
> mua** sản phẩm (đơn đã **giao thành công**) mới đánh giá được sản phẩm đó. Làm TỪNG BƯỚC,
> dừng chờ duyệt, không phá app cũ, comment tiếng Việt.

### Điều kiện đánh giá (LOGIC CỐT LÕI — làm đúng)

- Người dùng phải **đăng nhập**.
- Phải **đã mua** sản phẩm: tồn tại một dòng đơn hàng (OrderItem) thuộc Order của user đó,
  với **trạng thái đơn = giao hàng thành công** (delivered).
- **Nút "Đánh giá" xuất hiện ở trang "Đơn hàng của tôi"** (hoặc chi tiết đơn), CHỈ khi đơn
  đã giao thành công, cho từng sản phẩm trong đơn.
- Chỉ đánh giá được **đúng sản phẩm đã mua**; **mỗi sản phẩm đã mua đánh giá 1 lần** (chống spam).

### BƯỚC 1 — Model (app `reviews`)

- `Review`: `product` (FK), `user` (FK người đánh giá), `order_item` hoặc `order` (FK — bằng
  chứng đã mua), `rating` 1–5, `content`, `is_anonymous` (bool — ẩn danh), `created_at`,
  `sentiment` ('POS'/'NEU'/'NEG'), `sentiment_confidence` (float).
- `ReviewMedia`: FK `review`, `file`, `media_type` ('image'/'video') — nhiều ảnh/video mỗi đánh giá.
- Ràng buộc **unique** `(user, product)` (hoặc `(user, order_item)`) để mỗi lần mua đánh giá 1 lần.
- Tạo migration; giữ Product/Category/Order nguyên vẹn.

### BƯỚC 2 — Luồng đánh giá

- Trang **"Đơn hàng của tôi"**: mỗi đơn hiện trạng thái. Khi = **giao thành công** → hiện nút
  **"Đánh giá"** cho từng sản phẩm chưa đánh giá trong đơn.
- Bấm → form: chọn sao (1–5, widget bấm), nội dung, tải nhiều ảnh/video, **nút bật/tắt "Ẩn danh"**.
- **Kiểm tra phía server** trước khi lưu: đã đăng nhập + đã mua + đơn đã giao + chưa đánh giá sản
  phẩm này. Không thỏa → chặn (không cho đánh giá).

### BƯỚC 3 — Ẩn danh (đúng nghĩa người dùng mô tả)

- "Ẩn danh" là **nút bật/tắt lúc gửi đánh giá**. Nếu BẬT → khi **hiển thị** đánh giá, KHÔNG hiện
  tên user (hiện "Người dùng ẩn danh"). User vẫn đăng nhập, hệ thống vẫn biết là ai — chỉ **ẩn
  tên công khai**, không phải cho phép đánh giá mà không đăng nhập.

### BƯỚC 4 — Hiển thị & thống kê cho KHÁCH (sửa lại cho đúng)

- Trang chi tiết sản phẩm: **điểm sao trung bình** + **phân bố sao** (bao nhiêu 5★…1★) + tổng số
  đánh giá; danh sách đánh giá (tên hoặc "ẩn danh", sao, nội dung, ảnh/video, ngày).
- **Thống kê cảm xúc cho khách chỉ hiển thị TỈ LỆ PHẦN TRĂM**: **% tích cực**, **% tiêu cực**
  (và % trung lập), tính từ nhãn `sentiment` của các đánh giá sản phẩm đó. Ví dụ: "Tích cực 82%
  · Trung lập 10% · Tiêu cực 8%".
- **BỎ hoàn toàn nhãn "chưa chắc chắn" ở giao diện khách** (đây là chỗ bản trước ghi sai). Nếu
  vẫn muốn giữ ngưỡng độ tin cậy thì chỉ dùng **nội bộ / trang admin sau**, KHÔNG hiện cho khách.

### BƯỚC 5 — Tích hợp mô hình cảm xúc (đã train sẵn)

- Chép `sentiment_model.joblib` (xuất từ `sentiment_analysis_3lop.ipynb`) vào `reviews/ml/`.
- `reviews/ml/sentiment.py`: nạp model **một lần** (`@lru_cache`); `predict_sentiment(text)` tách
  từ bằng **underthesea `word_tokenize(text, format="text")` GIỐNG lúc train** → `vectorizer.transform`
  → `model.predict`; kèm độ tin cậy `predict_proba().max()`.
- Khi lưu đánh giá → gắn `sentiment` + `sentiment_confidence`.
- Thêm `underthesea`, `scikit-learn`, `joblib` vào `requirements.txt`; nạp model không làm chậm khởi động.

### BƯỚC 6 — Seed dữ liệu (giờ CẦN user + đơn hàng, vì mua mới đánh giá được)

Sản phẩm đã có (`seed_products.sql`). Vì đã đổi sang "mua mới đánh giá", seed phải tạo chuỗi đầy đủ:

- Nhiều **tài khoản user ảo**.
- Mỗi user có **đơn hàng ảo** mua **các sản phẩm khác nhau**, đặt trạng thái = **giao thành công**.
- **Đánh giá ảo** gắn với các đơn/sản phẩm đó: đa dạng sao (1–5) + nội dung khen/chê/trung lập
  (câu tiếng Việt thật về kính), một số bật **ẩn danh**. Tôn trọng ràng buộc unique (mỗi user
  chỉ đánh giá sản phẩm đã mua, 1 lần).
- Chạy `predict_sentiment` điền nhãn cảm xúc cho các đánh giá seed.
- Gói vào management command `seed_reviews` (tạo users + orders delivered + reviews + nhãn cảm xúc).

### BƯỚC 7 (tùy chọn) — Cải tiến notebook cảm xúc

Claude Code **có thể cải tiến `sentiment_analysis_3lop.ipynb` tốt hơn** nếu thấy hợp lý: ví dụ
thêm tiền xử lý (chuẩn hóa teencode/emoji/dấu câu), thêm đặc trưng (char n-gram), cân bằng dữ
liệu tốt hơn cho **lớp trung lập** (đang là lớp yếu nhất, F1 ~0.37), thử thêm mô hình, hoặc tinh
chỉnh tham số. **Giữ nguyên đầu ra** là `sentiment_model.joblib` chứa cả `vectorizer` + `model`
để tương thích với code Django ở Bước 5.

### Tự kiểm & dừng

- Curl: khách chưa mua KHÔNG đánh giá được; trang sản phẩm hiện sao trung bình + phân bố sao +
  % tích cực/tiêu cực (không có "chưa chắc chắn").
- **DỪNG — người dùng test**: đăng nhập tài khoản seed đã mua hàng → vào "Đơn hàng của tôi" (đơn
  đã giao) → đánh giá → kiểm tra ẩn danh ẩn tên đúng, nhãn cảm xúc đúng, thống kê % cập nhật.

---

## 31. NHẬT KÝ PHIÊN LÀM VIỆC — App `orders` (đặt hàng/checkout) làm nền cho mục 30

Trước khi làm BƯỚC 1 của mục 30 (model `Review` FK tới `order`/`order_item`), đã rà soát
toàn bộ codebase (accounts, products, cart, wallet, favorites) và phát hiện: **chưa có
khái niệm "đơn hàng" nào tồn tại** — không có app `orders`, không có model `Order`/
`OrderItem`, nút "Thanh toán" ở `cart.html` đang bị `disabled` với ghi chú "đang phát
triển", `wallet/views.py` chỉ là file rỗng. Mục 30 viết như thể Order đã có sẵn, nên đây
là một lỗ hổng phải lấp trước, không nằm trong 7 bước đã viết.

Đã hỏi người dùng hướng xây dựng, và chọn: **đơn giản hóa** — có luồng đặt hàng thật (trừ
ví điện tử), nhưng KHÔNG mô phỏng nhiều trạng thái vận chuyển; đơn vừa tạo được coi là đã
**giao hàng thành công** ngay.

### Đã làm

- Tạo app `orders` (thêm vào `INSTALLED_APPS` sau `cart`).
- `Order`: `user`, `status` (hiện chỉ có `DELIVERED` — giữ field để BƯỚC 1 kiểm tra đúng
  nghĩa "đơn đã giao thành công"), `total_amount`, `created_at`.
- `OrderItem`: `order`, `product`, `quantity`, `unit_price` (lưu giá tại thời điểm mua,
  không đổi theo giá sản phẩm hiện tại).
- `orders/views.py`: `checkout` (POST, `@login_required`) — kiểm tra giỏ không rỗng, đủ
  tồn kho, trừ ví qua `wallet.withdraw()` có sẵn, tạo `Order`+`OrderItem`, trừ tồn kho, xóa
  giỏ hàng, tất cả trong `transaction.atomic()`; `my_orders` — trang "Đơn hàng của tôi".
- Sửa `cart.html`: nút "Thanh toán" (trước đây `disabled`) giờ POST thật tới
  `orders:checkout`.
- Template `orders/my_orders.html` + CSS (`.order-card`, `.order-status`...) tái dùng lại
  class `.cart-item` có sẵn cho đồng bộ giao diện.
- Thêm link "Đơn hàng của tôi" ở header (cạnh tên user) và footer.
- Migration `orders/migrations/0001_initial.py`, đã `migrate` vào MySQL thật.

### Tự kiểm tra (đã chạy server thật + `curl`, không chỉ đọc code)

Nạp thử 5.000.000₫ vào ví tài khoản seed `Minh`, đăng nhập qua `curl` (giữ cookie session
thật), thêm 2x sản phẩm "Incantation" (1.651.000₫) vào giỏ, bấm "Thanh toán" thật:

- Đơn `#1` được tạo, `status = DELIVERED`, `total_amount = 3.302.000`.
- `OrderItem` đúng: `quantity=2`, `unit_price=1.651.000`.
- Ví bị trừ đúng: `5.000.000 → 1.698.000`, có `Transaction` loại `PAYMENT` ghi lại.
- Tồn kho sản phẩm giảm đúng: `19 → 17`.
- Giỏ hàng được xóa sạch sau khi đặt hàng (`cart_items_left = 0`).
- Trang "Đơn hàng của tôi" hiển thị đúng đơn, đúng sản phẩm, đúng trạng thái "Giao hàng
  thành công".

**DỪNG — chờ người dùng duyệt**: xác nhận hướng "đơn giản hóa" ở trên là đúng ý, rồi mới
tiếp tục BƯỚC 1-7 ở mục 30 (model `Review` + luồng đánh giá + tích hợp model cảm xúc +
seed dữ liệu).

---

## 32. NHẬT KÝ PHIÊN LÀM VIỆC — Notebook phân tích cảm xúc + BƯỚC 1-5 mục 30

Người dùng yêu cầu làm phần **phân tích cảm xúc trước** (đã tự chuẩn bị `phantichcamxuc/
data - data.csv` - 31.460 bình luận gán nhãn POS/NEU/NEG - và một notebook mẫu), sau đó mới
làm tiếp BƯỚC 1-4 (app `reviews`) rồi gắn model vào BƯỚC 5.

### Phần 1 - `phantichcamxuc/sentiment_analysis.ipynb`

Notebook mẫu ban đầu là bản Colab tiếng Anh, nhị phân, dùng file khác (2.000 dòng
`positive/negative`) - **không chạy được với dữ liệu thật của đồ án**, có cả lỗi cú pháp
(`assert ..., #comment`). Đã viết lại toàn bộ và **chạy thật** (không chỉ viết code suông)
bằng `jupyter nbconvert --execute`:

- Đọc `data - data.csv` cục bộ, làm sạch (chuẩn hóa dấu câu lặp, **bỏ 4.754 bình luận
  trùng lặp** - notebook mẫu không có bước này, nếu thiếu sẽ làm rò rỉ dữ liệu train/test),
  còn 26.706 dòng.
- Tách từ tiếng Việt bằng `underthesea.word_tokenize(..., format="text")`.
- TF-IDF (`ngram_range=(1,2)`, bỏ `stop_words="english"` sai ngôn ngữ của bản mẫu).
- So sánh 3 mô hình bằng **macro-F1** (không dùng accuracy vì lệch lớp): LogisticRegression
  **0.648** (chọn) > ComplementNB 0.626 > LinearSVC hiệu chỉnh 0.598. F1 lớp NEU của mô hình
  chọn = 0.405 (cải thiện so với ~0.37 ghi nhận trước đó).
- Lưu `sentiment_model.joblib` (dict `{vectorizer, model}`), đã kiểm tra load lại đúng.
- Đã thêm `scikit-learn`, `underthesea`, `joblib` vào `requirements.txt`.

### Phần 2 - BƯỚC 1-4 (app `reviews`)

- `Review` (product, user, `order_item` FK tới `orders.OrderItem`, rating 1-5, content,
  is_anonymous, sentiment, sentiment_confidence, `unique_together=(user, product)`) và
  `ReviewMedia` (nhiều ảnh/video mỗi đánh giá).
- `orders` app: thêm `reviewed_product_ids` vào `my_orders` view để trang "Đơn hàng của tôi"
  hiện nút "Đánh giá" đúng theo từng sản phẩm CHƯA đánh giá trong đơn đã giao thành công,
  hoặc badge "Đã đánh giá" nếu đã có.
- `reviews:create` view kiểm tra đủ 4 điều kiện phía SERVER (đăng nhập, order_item thuộc
  đúng user, đơn đã giao, sản phẩm chưa được đánh giá) trước khi cho lưu - không chỉ ẩn nút
  trên giao diện.
- "Ẩn danh": cờ bật/tắt lúc gửi, `Review.display_name` trả "Người dùng ẩn danh" khi hiển thị
  (user vẫn đăng nhập, hệ thống vẫn biết là ai).
- Trang chi tiết sản phẩm: điểm sao trung bình + phân bố sao + tổng số đánh giá + danh sách
  đánh giá (tên/ẩn danh, sao, nội dung, ảnh/video, ngày) - tính bằng **1 câu `aggregate()`
  duy nhất** (Count có `filter=Q(...)`) thay vì nhiều query COUNT() rời rạc.
- Thống kê cảm xúc cho khách CHỈ hiện % Tích cực/Trung lập/Tiêu cực, KHÔNG có nhãn "chưa
  chắc chắn" (đúng yêu cầu BƯỚC 4); `sentiment_confidence` chỉ lưu trong DB/admin.

### Phần 3 - BƯỚC 5 (gắn model vào)

- Copy `sentiment_model.joblib` vào `reviews/ml/`.
- `reviews/ml/sentiment.py`: `predict_sentiment(text)` - tiền xử lý (`clean_text` + tách từ
  underthesea) GIỐNG HỆT lúc train trong notebook, nạp model 1 lần bằng `@lru_cache`.
- Khi lưu đánh giá (`reviews/views.py`) → gọi `predict_sentiment()` gắn `sentiment` +
  `sentiment_confidence` ngay, người dùng không tự chọn nhãn.

### Tự kiểm tra bằng luồng thật (curl + MySQL, không chỉ đọc code)

Đăng nhập `Minh` → mua 2 sản phẩm thật qua checkout (trừ ví) → vào "Đơn hàng của tôi" thấy
đúng nút "Đánh giá" → gửi đánh giá 5★ ẩn danh kèm nội dung tích cực → **DB lưu đúng nhãn POS
98%**, trang sản phẩm hiện "Tích cực 100%", tên hiện "Người dùng ẩn danh". Gửi đánh giá thứ 2
(4★, không ẩn danh, kèm 1 ảnh thật qua `multipart/form-data`) → ảnh lưu đúng vào
`media/reviews/2026/09/`, hiển thị đúng trên trang sản phẩm. Thử gửi đánh giá lần 2 cho cùng
1 sản phẩm → bị chặn đúng với thông báo "Bạn đã đánh giá... rồi."

**Sự cố phát hiện & xử lý trong lúc test**: lần submit đầu tiên qua `curl` bị lỗi encode
(nội dung tiếng Việt lưu thành dấu `?`) do dùng `$(cat file)` trong Git Bash làm hỏng
byte UTF-8 khi đi qua biến shell - **không phải lỗi của Django/MySQL/model**. Xác minh lại
bằng cách đọc file trực tiếp qua `curl --data-urlencode name@file`/`-F name=<file` (không
qua biến shell) → lưu và hiển thị tiếng Việt có dấu hoàn toàn chính xác, sentiment dự đoán
đúng (POS 98%) khớp với demo trong notebook.

### Còn lại (chưa làm, không nằm trong yêu cầu lần này)

- BƯỚC 7 (tùy chọn) - cải tiến thêm notebook cho lớp NEU (hiện F1 0.405).

---

## 33. NHẬT KÝ PHIÊN LÀM VIỆC — Điều tra báo cáo lỗi CSS + BƯỚC 6 (seed_reviews)

### Điều tra "lỗi CSS" người dùng báo (đoạn text dán ra trông như không có định dạng)

Trước khi sửa mù, đã cài Edge headless (`--headless=new --screenshot=...`, chưa có sẵn công
cụ chụp màn hình trình duyệt trong máy) để **chụp ảnh THẬT** trang chi tiết sản phẩm thay vì
chỉ đọc code. Kết quả: khu vực "Đánh giá sản phẩm" render ĐÚNG hoàn toàn (lưới điểm số/thanh
phân bố sao/badge cảm xúc màu sắc đầy đủ, đã gửi ảnh cho người dùng xem). Kết luận: đoạn text
người dùng dán ra là do **copy-paste text từ trang** (paste luôn mất hết định dạng/màu/bố cục
dù trang render đúng), không phải lỗi CSS thật - không có gì phải sửa ở đây. Đã báo lại cho
người dùng, đề nghị hard refresh (Ctrl+Shift+R) hoặc gửi ảnh chụp màn hình thật nếu vẫn thấy
lỗi sau khi xác nhận.

### BƯỚC 6 - `reviews/management/commands/seed_reviews.py`

- 15 "khách hàng ảo" (username trông như người dùng thật, ví dụ `minhanh97`, nhận diện/dọn dẹp
  qua đuôi email `@seed.chuyendetn.local`, không lộ tiền tố kỹ thuật khi hiển thị công khai).
- Mỗi user mua TẤT CẢ sản phẩm đang bán (`is_active=True`) trong 1 đơn hàng, trạng thái tự
  động DELIVERED (đúng nghĩa "seed đơn giản hóa" đã chọn ở mục 31) - **không trừ tồn kho thật**
  (chủ ý khác với `orders/views.py` thật, vì seed chỉ để demo đánh giá, không mô phỏng kinh tế
  cửa hàng).
- Nội dung đánh giá lấy ngẫu nhiên từ 3 nhóm câu tiếng Việt thật (khen/chê/trung lập) theo
  đúng trọng số tỉ lệ nhãn của bộ dữ liệu huấn luyện thật (POS ~60%/NEU ~16%/NEG ~24%) - nhãn
  cảm xúc thật sự do `predict_sentiment()` dự đoán ra (đúng yêu cầu, KHÔNG gán tay).
- `--reset`: xóa sạch user ảo cũ (nhận theo đuôi email) rồi seed lại từ đầu.

**Lỗi phát hiện khi tự kiểm tra (không chỉ chạy 1 lần rồi báo xong)**: chạy lệnh lần 2 để
kiểm tra idempotent thì phát hiện vẫn tạo thêm 15 đơn hàng RỖNG dù không tạo đánh giá mới
(do code tạo `Order` cho MỌI user trước, rồi mới lọc sản phẩm chưa đánh giá theo từng đơn) -
sửa lại: lọc `pending_products` (sản phẩm user chưa đánh giá) TRƯỚC, chỉ tạo `Order` khi danh
sách này không rỗng. Xác minh lại bằng `--reset` + chạy 2 lần liên tiếp: lần 2 đúng 0 đơn/0
đánh giá mới được tạo.

**Kết quả sau khi seed** (kiểm tra trực tiếp trong MySQL + chụp ảnh trang sản phẩm thật):
45 đánh giá mới, ví dụ Incantation 16 đánh giá/điểm TB 3,1 (Tích cực 56% · Trung lập 6% ·
Tiêu cực 38%) - trang hiển thị đúng với khối lượng dữ liệu lớn, không phát sinh lỗi CSS/layout
nào ở quy mô này.

---

## 34. NHẬT KÝ PHIÊN LÀM VIỆC — Sửa 3 lỗi trong BUG.ipynb + hoàn thiện UX đánh giá/cảm xúc

Yêu cầu mới: `PROMPT_VirtualTryOn_ClaudeCode.md` là nơi người dùng tập trung TOÀN BỘ yêu cầu
từ giờ trở đi (bao gồm module try-on gốc + một danh sách lớn các yêu cầu khác đã dán thêm ở
cuối file - xem mục "Còn lại" bên dưới). Yêu cầu lần này: sửa lỗi trong `BUG.ipynb`, rồi hoàn
thiện UX đánh giá/cảm xúc theo mô tả chi tiết mới.

### Sửa lỗi trong BUG.ipynb (đã trích ảnh đính kèm ra xem trực tiếp, không đoán từ mô tả)

1. **Checkout sập `RelatedObjectDoesNotExist: User has no wallet`** (tài khoản `admin`) - nguyên
   nhân gốc: `accounts/signals.py` chỉ tự tạo Wallet/Cart/Favorite cho user MỚI tạo
   (`created=True`), tài khoản có từ TRƯỚC signal (ví dụ superuser tạo lúc mới dựng dự án)
   không có các bản ghi này. Đã sửa 2 lớp: (a) `orders/views.py` dùng
   `Wallet.objects.get_or_create()` thay vì `request.user.wallet` trực tiếp; (b) thêm
   management command `accounts/management/commands/backfill_profiles.py` quét bù cho MỌI user
   đang thiếu - đã chạy, bù được 1 wallet (admin) + 4 favorite. Xác minh lại: tài khoản `admin`
   checkout thành công thật (đơn #48).
2. **Nút "Cập nhật" trong giỏ hàng vỡ CSS** - nguyên nhân gốc: `cart.html` đặt CẢ 2 class
   `quantity-stepper cart-item-qty` lên chung 1 `<form>` chứa 4 phần tử (−, input, +, nút "Cập
   nhật"), khiến rule `.quantity-stepper button` (chỉ định cho nút −/+, có specificity cao hơn
   `.btn`) vô tình đè `width/height/border/background` lên nút "Cập nhật". Đã tách: `<form
   class="cart-item-qty">` bọc thêm 1 `<div class="quantity-stepper">` CHỈ chứa −/input/+, nút
   "Cập nhật" nằm ngoài div đó. Xác minh lại bằng cấu trúc HTML thật trả về.
3. **Sao đánh giá luôn hiện đủ 5 sao đầy** - nguyên nhân gốc: sao đầy/rỗng dùng CHUNG ký tự
   "★", chỉ phân biệt bằng MÀU CSS (`.star.is-filled`) - nếu CSS chưa kịp cập nhật/cache cũ thì
   mọi sao trông giống hệt nhau. Đã đổi sang dùng 2 ký tự khác nhau (★ đầy / ☆ rỗng) ở cả trang
   sản phẩm và widget chọn sao lúc đánh giá - đúng ngay cả khi CSS lỗi. Đã thêm `?v=2` vào link
   `style.css` trong `base.html` để chống cache CSS cũ (nghi vấn là nguyên nhân gây ra một phần
   các lỗi hiển thị đã gặp trước đó, bao gồm cả báo cáo "lỗi css" ở phiên trước).

### Hoàn thiện UX đánh giá + cảm xúc (theo mô tả chi tiết mới của người dùng)

- **Ô đánh giá chuyển vào NGAY TRANG SẢN PHẨM** (không còn trang `/danh-gia/tao/...` riêng
  nữa): `products/views.py` tính `can_review` (đã đăng nhập + có `OrderItem` đã giao thành công
  cho sản phẩm này + chưa đánh giá) và truyền `ReviewForm` vào context; `detail.html` render
  form ngay trong khu vực `#danh-gia` KHI VÀ CHỈ KHI `can_review` đúng.
- Nút "Đánh giá" ở "Đơn hàng của tôi" đổi hướng: giờ trỏ tới `products:detail` (kèm
  `#danh-gia`) thay vì trang riêng.
- `reviews/views.py` viết lại: chỉ còn xử lý POST (lưu đánh giá) rồi quay lại đúng trang sản
  phẩm; xóa `templates/reviews/review_form.html` (không còn view nào render nó).
- **Nhãn cảm xúc RIÊNG TƯ trên từng đánh giá** (Tích cực/Trung lập/Tiêu cực) - CHỈ hiện với
  chính người viết đánh giá đó và admin (`request.user.is_staff or request.user == review.user`
  trong template), khác hẳn với % TỔNG HỢP công khai ai cũng thấy. Xác minh bằng số lượng badge
  thực tế trả về: admin thấy 19 (3 tổng hợp + 16 riêng từng đánh giá), user thường `Minh` thấy 4
  (3 tổng hợp + 1 của chính họ), khách vãng lai chỉ thấy 3 (chỉ tổng hợp).
- **Thống kê tích cực/tiêu cực bên trang admin**: `ReviewAdmin.changelist_view()` override,
  hiển thị box thống kê qua template `templates/admin/reviews/review/change_list.html`.
  **Lỗi phát hiện khi tự kiểm tra**: lần đầu tổng 48 đánh giá nhưng cộng dồn ra có 3 (1+1+1) -
  nguyên nhân là `.values("sentiment").annotate(Count("id"))` chạy trên queryset đã có sẵn
  `order_by("-created_at")` (kế thừa từ `Review.Meta.ordering`), khiến Django tự thêm
  `created_at` vào GROUP BY (lỗi kinh điển của Django ORM) - gần như mỗi dòng thành 1 nhóm riêng.
  Sửa bằng `.order_by()` (xóa sắp xếp) trước khi `.values().annotate()`. Xác minh lại: 28+7+13 = 48, khớp.

### Tự kiểm tra bằng luồng thật (curl, không chỉ đọc code)

Đăng nhập `admin` → nạp ví → thêm giỏ hàng → **checkout thành công** (trước đây sập 500) → vào
"Đơn hàng của tôi" thấy nút "Đánh giá" trỏ đúng `/san-pham/.../#danh-gia` → trang sản phẩm hiện
đúng form đánh giá inline (action trỏ đúng `order_item_id`) → gửi đánh giá → redirect đúng về
lại trang sản phẩm kèm anchor. Đếm số badge cảm xúc trả về theo từng vai trò (admin/user
thường/khách vãng lai) để xác nhận đúng phạm vi riêng tư. Kiểm tra cấu trúc HTML thật của giỏ
hàng (nút "Cập nhật" đã ra khỏi `.quantity-stepper`) và ký tự sao thật trả về (mix ★/☆ đúng
theo rating, không còn luôn 5 sao đầy).

### Còn lại (chưa làm - danh sách rất dài trong `PROMPT_VirtualTryOn_ClaudeCode.md`, CHƯA hỏi
người dùng ưu tiên cái nào trước)

Đổi slide trang chủ + tên site "Astraea" + màu chủ đạo xanh đen-trắng, thêm phân loại kính
oval, xóa SQL seed dư thừa, kiểm CRUD admin, đổi theme admin xanh navy-trắng, giả lập thanh
toán chọn hình thức, sửa design "danh mục nổi bật", crawl thêm ảnh sản phẩm kính oval từ
carfia.com, ô tìm kiếm hoạt động thật, nút yêu thích ở product card + trang danh sách yêu
thích, AJAX giỏ hàng (không reload), giỏ hàng cho khách vãng lai (session/cookie), hủy đơn hàng
khi đang chờ xác nhận, bộ lọc giá/dáng gọng/giới tính, hoàn trả tồn kho khi hủy đơn, trang
profile cá nhân. Đây là khối lượng công việc rất lớn, không nằm trong yêu cầu cụ thể của phiên
này (chỉ có "sửa BUG.ipynb" + "phần cảm xúc/đánh giá" được nêu rõ) - cần hỏi người dùng thứ tự
ưu tiên trước khi làm tiếp, tránh đoán sai trọng tâm.

**Cập nhật**: người dùng từ chối câu hỏi ưu tiên, chỉ đạo thẳng: làm hết `BUG.ipynb` trước,
xong thì làm tiếp danh sách trong `PROMPT_VirtualTryOn_ClaudeCode.md` THEO ĐÚNG THỨ TỰ (không
hỏi lại) - xem mục 35.

---

## 35. NHẬT KÝ PHIÊN LÀM VIỆC — BUG.ipynb đợt 2 (người dùng bổ sung thêm lỗi + ảnh)

Người dùng đã điền thêm nội dung mới vào `BUG.ipynb` (kèm ảnh đính kèm - đã trích xuất ra xem
trực tiếp bằng script Python, không đoán từ mô tả) và yêu cầu: sửa hết lỗi trong đó trước, sau
đó làm tiếp tuần tự danh sách trong `PROMPT_VirtualTryOn_ClaudeCode.md`.

### Lỗi phát hiện & đã sửa

1. **Bug tự gây ra ở phiên trước - comment Django nhiều dòng bị lộ ra thành TEXT THẬT trên
   trang** (ảnh chụp cho thấy rõ `{# Nhãn cảm xúc riêng tư: ... #}` hiện nguyên văn trên mọi
   đánh giá, và đoạn comment `?v=` ở `base.html` hiện phía trên header). Nguyên nhân gốc: cú
   pháp comment 1 dòng `{# ... #}` của Django **không hỗ trợ xuống dòng** - nếu nội dung comment
   trải dài nhiều dòng, Django không nhận ra đó là comment nữa mà in ra y nguyên dạng text. Sửa
   bằng cách đổi toàn bộ 3 chỗ dùng `{# #}` nhiều dòng (2 ở `detail.html`, 1 ở `base.html`)
   sang `{% comment %}...{% endcomment %}` (hỗ trợ nhiều dòng). Đã quét lại toàn bộ `templates/`
   xác nhận không còn `{#` nào sót.
2. **Nút giỏ hàng (icon) ở lưới sản phẩm trang chủ không hoạt động** - nguyên nhân: chỉ là
   `<button type="button">` trơ, không nằm trong form, không có JS xử lý - hoàn toàn chưa được
   nối logic. Sửa bằng cách bọc `<form action="{% url 'cart:add' %}" method="post">` (đúng
   pattern đã dùng ở trang chi tiết sản phẩm), chỉ hiện khi còn hàng.
3. **Đổi luồng thanh toán sang GIẢ LẬP** (yêu cầu rõ ràng của người dùng): trước đây thanh toán
   trừ thẳng số dư Ví điện tử - nhưng user thường không có cách nạp ví (chưa xây trang nạp),
   nên MỌI tài khoản mới đều bị chặn ở bước này (đúng lỗi "Số dư không đủ" trong ảnh). Đã xây
   modal chọn hình thức thanh toán (COD/MoMo/Thẻ - thêm field `Order.payment_method`), bấm "Xác
   nhận thanh toán" là coi như thành công ngay, **không kiểm tra/trừ ví nữa**; xóa dòng chữ
   "Thanh toán bằng số dư trong Ví điện tử". Modal tái dùng đúng pattern `.tryon-modal` sẵn có
   (kể cả chỗ `[hidden]` phải khai riêng để thắng rule `display:flex` - bài học đã ghi sẵn trong
   comment CSS của `.tryon-modal` từ trước, áp dụng lại cho `.payment-modal`).
4. **Tài khoản admin bị coi như khách hàng bình thường** - đã sửa `accounts/views.py`: đăng
   nhập bằng tài khoản `is_staff` (không có `?next=`) sẽ vào thẳng `/admin/` thay vì trang chủ
   khách hàng (admin vẫn bấm "XEM TRANG WEB" được nếu muốn thao tác như khách).
5. **Thống kê cảm xúc ở trang admin nâng lên thành biểu đồ chi tiết từng sản phẩm** - thêm biểu
   đồ cột (CSS thuần - đúng triết lý "không phụ thuộc thư viện ngoài" đã ghi sẵn ở đầu
   `style.css`, không thêm Chart.js) hiển thị % tích cực/trung lập/tiêu cực theo từng sản phẩm,
   bên cạnh box thống kê tổng đã có.

**Chưa làm** (cố ý hoãn, không phải bỏ sót): yêu cầu "css lại phần lọc" ở trang admin khá mơ hồ
từ ảnh tĩnh (bản thân bộ lọc mặc định của Django admin hiển thị đúng, không thấy lỗi rõ ràng) -
trùng với hạng mục "đổi theme admin xanh navy-trắng" đã có sẵn trong danh sách
`PROMPT_VirtualTryOn_ClaudeCode.md`, nên gộp làm 1 lần cho nhất quán thay vì sửa chắp vá 2 lần.

---

## 36. NHẬT KÝ PHIÊN LÀM VIỆC — Bắt đầu danh sách PROMPT_VirtualTryOn_ClaudeCode.md (mục 1: rebrand Astraea)

Sau khi xong `BUG.ipynb`, chuyển sang làm TUẦN TỰ danh sách "yêu cầu" ở cuối
`PROMPT_VirtualTryOn_ClaudeCode.md` theo đúng chỉ đạo của người dùng. Mục đầu tiên: đổi ảnh nền
slide trang chủ, bỏ phần trang trí thừa (chỉ giữ 2 nút), thêm danh mục Oval, đổi tên site thành
"Astraea", đổi màu chủ đạo sang xanh navy đậm + trắng.

### Đã làm

- Tải đúng ảnh nền từ URL người dùng cung cấp (`wallpaperaccess.com/full/1753197.jpg` - kính
  râm trên nền biển) vào `static/img/hero-bg.jpg`, dùng làm background thật cho `.hero` (phủ
  gradient navy đậm lên trên để chữ trắng luôn đọc rõ).
- Xóa toàn bộ phần trang trí quanh hero (tag "Ưu đãi khai trương", 3 thẻ nổi "Giao hàng
  nhanh/Thanh toán an toàn/Đánh giá 4.8", hàng thống kê số liệu) - chỉ giữ tiêu đề, mô tả ngắn,
  và ĐÚNG 2 nút "Xem ngay" / "Danh mục" như yêu cầu. Dọn theo CSS chết tương ứng
  (`.hero-eyebrow`, `.hero-stats`, `.hero-visual`, `.hero-card-stack`, `.hero-blob`,
  `.hero-float-card*`) vì không còn template nào dùng tới.
- Thêm danh mục `Category(name="Oval", slug="oval")` - đã hiện đúng trong danh mục nổi bật +
  bộ lọc dáng kính (0 sản phẩm - phần gán sản phẩm oval thật sẽ làm ở mục crawl carfia.com kế
  tiếp trong danh sách).
- Đổi toàn bộ "ChuyenDeTN"/"ChuyenDeTN Shop" → "Astraea" (title mọi trang, meta description,
  logo header/footer, "Về Astraea", dòng bản quyền, thông báo chào mừng lúc đăng ký) - quét lại
  xác nhận không còn sót.
- Đổi bảng màu `:root` trong `style.css` sang xanh navy đậm + trắng (`--color-primary:
  #0b1e3f`, `--color-accent: #1d4ed8` xanh dương đậm hơn để vẫn phân biệt được nút CTA/giá tiền
  với nền navy, `--color-surface: #fff`). Nhờ toàn bộ site đã dùng CSS custom properties từ
  đầu, đổi đúng 1 chỗ này là lan ra toàn site. Qué và sửa thêm 2 chỗ lỡ hardcode màu cũ thay vì
  dùng biến (`.category-avatar` gradient mint cũ, `.newsletter` gradient teal cũ) - grep lại
  toàn file xác nhận không còn hex màu cũ nào sót.

### Tự kiểm tra bằng ảnh chụp thật (Edge headless, không đoán qua code)

Chụp lại trang chủ (đầy đủ từ hero tới footer) và trang chi tiết sản phẩm sau khi sửa - xác
nhận toàn bộ nhất quán: hero hiện đúng ảnh + đúng 2 nút, danh mục "Oval" xuất hiện, logo/tên
"Astraea" đúng khắp nơi, không còn màu teal/cam cũ sót lại ở bất kỳ đâu (category avatar,
newsletter, giá tiền, nút, badge tồn kho).

### Đã tìm lại được ảnh `img.png`/`img_1.png` (nằm sẵn trong thư mục dự án, không phải thiếu)

Ghi nhầm ở trên là thiếu ảnh - thực ra `img.png`/`img_1.png`/`img_2.png` nằm sẵn ở gốc dự án
(người dùng lưu kèm khi viết prompt). Đã mở xem trực tiếp và phát hiện thêm 2 việc cần sửa
ngay:

1. **`img.png` - lỗi nghiêm trọng: nút "Thêm vào giỏ hàng" ở trang chi tiết sản phẩm phồng to
   thành khối bầu dục khổng lồ**, đè lên cả nút tăng giảm số lượng. Nguyên nhân gốc: icon SVG
   bên trong nút không có `width`/`height` khai báo ở đâu cả - toàn bộ icon khác trong site đều
   có riêng 1 rule kích thước (`.icon-link svg`, `.icon-btn svg`...) nhưng `.btn` (class dùng
   chung cho MỌI nút) thì thiếu, nên trình duyệt áp kích thước mặc định cho SVG "thay thế"
   (300×150px) khi không có gì ràng buộc, kéo phồng cả nút theo icon. Sửa bằng cách thêm
   `.btn svg { width: 18px; height: 18px; }` dùng chung - vừa sửa đúng chỗ lỗi, vừa phòng lặp
   lại ở bất kỳ nút nào khác sau này. (Trong lúc sửa tự gõ nhầm thiếu dấu đóng comment CSS
   `*/`, phát hiện ngay bằng cách đếm số `/*` và `*/` trong file phải bằng nhau - đã sửa trước
   khi test.)
2. **`img_1.png` - "Danh mục nổi bật" chỉ có 1 danh mục nằm lọt thỏm giữa lưới 6 cột trống
   trải, vòng tròn chỉ hiện chữ cái đầu thay vì ảnh kính thật**. Sửa 2 phần: (a) lấy ảnh sản
   phẩm mới nhất còn active trong từng danh mục làm ảnh đại diện thật (danh mục nào chưa có ảnh
   thì mới hiện lại chữ cái); (b) đổi `.category-grid` từ `repeat(6, 1fr)` cố định sang
   `repeat(auto-fit, minmax(140px, 180px))` để tự co gọn theo đúng số danh mục hiện có, không
   để trống cột khi ít danh mục - dọn theo 2 rule responsive cũ giờ dư thừa.

**Tự kiểm tra**: chụp ảnh Edge headless lại trang chi tiết sản phẩm - nút "Thêm vào giỏ hàng"
đã về đúng kích thước bình thường; chụp lại trang chủ - "Vuông (Square)" hiện đúng ảnh kính
thật trong vòng tròn, "Oval" (chưa có sản phẩm) vẫn hiện chữ cái dự phòng đúng như thiết kế,
lưới danh mục gọn lại thành cụm 2 thẻ thay vì dàn trải 6 cột trống. (Gặp 1 lần server dev chạy
`--noreload` chưa nạp code Python mới sau khi sửa `views.py` - phải khởi động lại server mới
thấy đúng, không phải lỗi code.)

`img_2.png` hóa ra chính là ảnh chụp THẬT của lỗi "css" người dùng báo ở lượt chat trước (mục
33 nghi là do copy-paste text, không phải lỗi thật) - ảnh này xác nhận lúc đó trang ĐÃ render
hoàn toàn không có CSS thật (đúng như nghi vấn ban đầu, trước khi bị bác bỏ nhầm). Nội dung ảnh
khớp 100% với review test đầu tiên (Minh, ẩn danh, 5 sao, "Chất lượng sản phẩm tuyệt vời...") -
tức ảnh chụp NGAY SAU lúc mới xây xong khu vực đánh giá (mục 32), TRƯỚC KHI có `?v=2` chống
cache CSS (thêm ở mục 34) - vậy nguyên nhân đúng là cache trình duyệt giữ bản `style.css` cũ
chưa có các class `.review-*` mới, đã được xử lý triệt để bằng `?v=` rồi, không cần sửa gì thêm.

### Còn lại trong danh sách PROMPT

Toàn bộ danh sách bổ sung ở cuối PROMPT_VirtualTryOn_ClaudeCode.md đã hoàn thành (mục 32-44).

---

## 44. NHẬT KÝ PHIÊN LÀM VIỆC — 6 tính năng cuối cùng của backlog PROMPT

Người dùng yêu cầu "làm tất cả" phần còn lại trong 1 lượt: giỏ hàng khách vãng lai, AJAX giỏ
hàng, bộ lọc giá, hủy đơn hàng + tự động hoàn tồn kho, trang profile cá nhân.

### 1) Giỏ hàng khách vãng lai (`cart/models.py`, `cart/views.py`, `cart/services.py`)

`Cart.user` đổi sang `null=True, blank=True`, thêm `Cart.session_key` (unique, null=True) - giỏ
hàng giờ gắn với TÀI KHOẢN hoặc với PHIÊN LÀM VIỆC (session). Viết `_get_cart(request, create)`
làm nguồn xác định DUY NHẤT "giỏ hàng của request này là giỏ nào", dùng chung cho mọi view
(`cart_view`/`cart_add`/`cart_update`/`cart_remove` - bỏ hết `@login_required` khỏi các view
này). `cart/services.py::merge_guest_cart_into_user()` gộp giỏ khách vãng lai vào giỏ tài khoản
ngay sau khi đăng nhập/đăng ký (`accounts/views.py`).

**Bug tự phát hiện qua test, đã sửa:** lúc đầu gọi `merge_guest_cart_into_user(request, user)`
SAU khi gọi `login()` khiến gộp giỏ luôn thất bại (badge vẫn về 0) - nguyên nhân: Django tự
XOAY VÒNG `session.session_key` mỗi lần `login()` thành công (chống session fixation), nên đọc
`request.session.session_key` sau `login()` luôn ra khóa MỚI, không khớp giỏ khách vãng lai đã
tạo trước đó. Sửa: lấy `session_key` TRƯỚC khi gọi `login()`, truyền thẳng vào hàm gộp.

Bước "Đặt hàng" vẫn BẮT BUỘC đăng nhập như cũ: trang giỏ hàng hiện nút "Đăng nhập để thanh toán"
thay vì nút "Thanh toán" khi chưa đăng nhập (modal thanh toán không render cho khách vãng lai).

### 2) AJAX giỏ hàng (`cart/views.py`, `static/js/main.js`, `templates/cart/cart.html`)

`cart_update`/`cart_remove` trả `JsonResponse` khi request kèm header
`X-Requested-With: XMLHttpRequest` (JS tự gắn), giữ nguyên hành vi redirect+flash message cũ
khi không có header này. `initAjaxCart()` trong main.js chặn submit của 2 form trong mỗi dòng
giỏ hàng, gọi `fetch()`, cập nhật DOM tại chỗ (giá dòng, tạm tính, tổng cộng, badge header qua
`data-item-total`/`data-cart-subtotal`/`data-cart-total-count`/`data-cart-badge`) - KHÔNG tải
lại trang. Trường hợp xóa hết sản phẩm cuối cùng: `location.reload()` cho đơn giản, để server tự
render đúng khối "Giỏ hàng đang trống".

### 3) Bộ lọc giá (`templates/products/home.html`, `static/js/main.js`, `_product_card.html`)

Thêm `<select data-price-filter>` với 4 khoảng giá cố định kiểu e-commerce VN (dưới 1tr, 1-2tr,
2-3tr, trên 3tr), thẻ sản phẩm có thêm `data-price="{{ product.price }}"`. Lọc client-side, kết
hợp AND với 2 bộ lọc giới tính/dáng kính đã có sẵn từ trước (dùng chung 1 hàm `apply()`).

**Bug có sẵn tự phát hiện khi test (không liên quan tính năng mới), đã sửa:** chip
"Dáng kính: X ×" LUÔN hiển thị dù chưa lọc gì, vì `.active-filter-chip` thiếu rule
`.active-filter-chip[hidden] { display: none; }` - thuộc tính HTML `hidden` chỉ ẩn được phần tử
nhờ rule mặc định `[hidden]{display:none}` của trình duyệt, và rule `.active-filter-chip {
display: inline-flex }` (cùng độ đặc tả) đứng SAU nên thắng, đè mất `hidden`. Đúng lỗi cùng loại
đã từng gặp và sửa ở `.tryon-modal`/`.payment-modal` (xem mục các lần fix trước) nhưng lúc đó bỏ
sót `.active-filter-chip`. Đã rà lại TOÀN BỘ phần tử dùng thuộc tính `hidden` trong dự án
(`grep " hidden>"`) để xác nhận không còn phần tử nào khác bị lỗi tương tự.

### 4) Hủy đơn hàng + tự động hoàn tồn kho (`orders/models.py`, `orders/views.py`, `my_orders.html`)

Thêm `Order.Status.CANCELLED`. View `cancel_order` (POST, login_required, chỉ cho hủy đơn của
chính mình, chặn hủy 2 lần) dùng `transaction.atomic()` để vừa đổi status vừa CỘNG LẠI
`stock_quantity` cho từng sản phẩm trong đơn - toàn bộ hoặc không có gì thay đổi. Nút "Hủy đơn
hàng" ở trang "Đơn hàng của tôi" chỉ hiện với đơn chưa hủy, có `data-confirm` (hàm
`initConfirmForms()` mới trong main.js - dùng chung `window.confirm()` cho mọi form có thuộc
tính này, không viết `onclick` rải rác). Đơn đã hủy không còn tính là "đã mua" khi xét quyền
đánh giá sản phẩm (`products/views.py::can_review` chỉ đếm đơn `status=DELIVERED`).

### 5) Trang profile cá nhân (`accounts/forms.py::ProfileForm`, `accounts/views.py::profile_view`)

Form chỉnh họ tên/email/SĐT/địa chỉ/avatar (không đổi username/mật khẩu - ngoài phạm vi). Icon
người dùng ở header (`.user-chip`, trước là `<span>` tĩnh) giờ là link `<a>` trỏ tới
`/accounts/ho-so/`. Địa chỉ/SĐT lưu ở đây được điền sẵn khi mở modal thanh toán (dùng lại đúng
`user.address`/`user.phone_number` đã có từ trước).

### Tự kiểm tra bằng luồng thật (không chỉ đọc code)

Viết 2 script Python (`requests`, tự đăng ký tài khoản test) + 1 script Playwright (Edge thật,
`channel="msedge"`) chạy lại NHIỀU LẦN cho tới khi pass hết:
- Giỏ khách vãng lai: thêm hàng khi CHƯA đăng nhập → badge đúng → AJAX cập nhật/xóa trả đúng
  JSON → đăng ký tài khoản mới → giỏ hàng khách vãng lai tự gộp đúng số lượng vào tài khoản.
- AJAX giỏ hàng qua click thật: bấm +/- rồi "Cập nhật" → xác nhận trang KHÔNG điều hướng
  (theo dõi sự kiện `framenavigated`) mà DOM vẫn cập nhật đúng giá/badge; xóa dòng cuối → tải
  lại đúng về trạng thái trống.
- Bộ lọc giá qua `select_option` thật + đếm `.product-card:visible`; xác nhận chip dáng kính chỉ
  hiện sau khi bấm chọn, ẩn lại đúng sau khi bấm nút xóa lọc (sau khi sửa bug ở mục 3).
- Đặt hàng qua modal thật → tồn kho giảm đúng số lượng → bấm "Hủy đơn hàng" (qua `confirm()`
  dialog thật, không phải giả lập) → tồn kho hoàn trả về ĐÚNG số ban đầu → hủy lần 2 báo lỗi,
  tồn kho không đổi thêm lần nữa.
- Trang hồ sơ: cập nhật họ tên/SĐT/địa chỉ → lưu → hiển thị lại đúng giá trị vừa lưu.

**Sự cố ngoài ý muốn trong lúc debug, đã khắc phục:** dùng PowerShell `Get-Content -Raw | ...
| Set-Content -Encoding utf8` để chèn thử 1 chuỗi đánh dấu vào `cart.html` nhằm kiểm tra server
có đọc lại template mới không - lệnh này đọc file bằng bảng mã ANSI mặc định thay vì UTF-8, làm
HỎNG toàn bộ ký tự tiếng Việt có dấu trong file (biến thành mojibake). Phát hiện ngay qua
system-reminder báo "file changed on disk", đã dùng lại tool Write để ghi đè toàn bộ nội dung
đúng bằng UTF-8 (dựng lại từ nội dung đã biết trước đó), xác nhận lại bằng `grep` sau khi sửa.
**Bài học:** không dùng PowerShell `Get-Content`/`Set-Content` để sửa file chứa tiếng Việt/UTF-8
- luôn dùng tool Edit/Write của Claude Code (đã xử lý đúng encoding) thay vì lệnh shell tự viết.

migrate 2 migration mới (`cart.0002_cart_session_key_alter_cart_user`,
`orders.0005_alter_order_status`) - `manage.py check` sạch, `makemigrations --check --dry-run`
không còn gì treo.

---

## 43. NHẬT KÝ PHIÊN LÀM VIỆC — Nút yêu thích + trang danh sách yêu thích

App `favorites` đã có sẵn model `Favorite` (1-1 với User, tự tạo qua signal) từ trước nhưng
`views.py`/`urls.py` mới chỉ là file rỗng, link "Yêu thích" ở header vẫn trỏ `href="#"`. Xây
đầy đủ:

- `favorites/views.py`: `toggle` (POST, bật/tắt yêu thích 1 sản phẩm, dùng `next` do CHÍNH
  template điền = đường dẫn trang hiện tại nên an toàn, không phải tham số người dùng tự do) +
  `list_view` (trang danh sách).
- `favorites/context_processors.py::favorites_summary` - bơm `favorite_count` vào MỌI template
  để hiện badge số lượng ở header, giống hệt cách `cart_summary` đã làm cho giỏ hàng.
- `templates/products/_favorite_button.html` - nút trái tim dùng CHUNG (tránh viết lặp), nhận
  `product` + `favorite_product_ids` (tập id đã tính sẵn 1 lần/trang ở view, tránh N+1 query
  khi 1 trang có nhiều thẻ sản phẩm) từ context; người chưa đăng nhập thấy link dẫn tới đăng
  nhập kèm `next` thay vì nút submit.
- Gắn nút này vào: thẻ sản phẩm dùng chung (`_product_card.html` - góc phải ảnh, tách riêng
  `<form>` ra khỏi `<a>` bọc ảnh để tránh lồng phần tử tương tác không hợp lệ trong HTML), trang
  chi tiết sản phẩm (cạnh nút "Thêm vào giỏ hàng"), và cả trang danh sách yêu thích (dùng lại
  đúng `_product_card.html`).
- Nối link "Yêu thích" ở header + footer (trước đó `href="#"`) vào URL thật, thêm badge số
  lượng giống giỏ hàng.

**Tự kiểm tra bằng luồng thật** (POST trực tiếp + Playwright click thật): toggle thêm → badge
tăng đúng, hiện đúng trong trang danh sách, nút chuyển trạng thái "is-active" (tim đỏ) + đổi
nhãn "Bỏ khỏi yêu thích"; toggle lại lần 2 → bỏ đúng, badge giảm, trang danh sách hiện lại đúng
trạng thái rỗng. Chụp ảnh xác nhận cả 3 vị trí (trang chủ, trang chi tiết, trang danh sách yêu
thích) đều hiển thị và hoạt động đúng qua click thật, không chỉ đọc code.

---

## 42. NHẬT KÝ PHIÊN LÀM VIỆC — Thêm tên người nhận + xây tính năng tìm kiếm thật

### Tên người nhận

Bổ sung `Order.recipient_name` (migration `0004`) - cùng nhóm với địa chỉ/SĐT đã làm ở mục 41,
bắt buộc nhập ở server (không chỉ HTML `required`), điền sẵn từ `user.get_full_name` (hoặc
username nếu chưa đặt tên) trong modal thanh toán. Test lại đúng 2 nhánh: thiếu tên bị chặn, đủ
thông tin lưu đúng vào đơn hàng (xác nhận trực tiếp trong CSDL).

### Ô tìm kiếm (mục tiếp theo trong danh sách PROMPT)

- Tách khối HTML thẻ sản phẩm ra `templates/products/_product_card.html` dùng chung (trước đó
  lặp y hệt trong `home.html`, giờ dùng `{% include %}` - tránh phải sửa 2 chỗ mỗi khi đổi giao
  diện thẻ sản phẩm, dùng lại được luôn cho trang tìm kiếm mới).
- `products/views.py::search()` - lọc theo `name`/`description`/`category__name` chứa từ khóa
  (`icontains`, không phân biệt hoa/thường), dùng GET (không phải POST) đúng chuẩn cho 1 hành
  động tìm kiếm (có thể copy link, bấm Back hoạt động đúng).
- Nối form tìm kiếm ở header (`base.html`, trước đó `action="#"` không đi đâu cả) vào URL thật;
  trang kết quả có thêm 1 ô tìm kiếm riêng để tìm lại nhanh, tự hiện dù ở màn hình nhỏ (rule
  CSS ẩn ô tìm kiếm header trên mobile trước đó vô tình khớp luôn ô này, đã tách riêng bằng
  thêm 1 class).

**Tự kiểm tra bằng luồng thật**: test tìm theo tên sản phẩm, theo tên danh mục, từ khóa không
khớp gì (đúng hiện trạng thái rỗng), để trống (hiện toàn bộ sản phẩm). Phát hiện thú vị lúc
chụp ảnh xác nhận: gõ "kinh" (không dấu) vẫn tìm ra đúng sản phẩm có "kính" (có dấu) trong mô
tả - do collation `utf8mb4_unicode_ci` của MySQL tự so khớp không phân biệt dấu, một hiệu ứng
phụ có lợi cho tìm kiếm tiếng Việt chứ không cần code thêm gì.

---

## 41. NHẬT KÝ PHIÊN LÀM VIỆC — Địa chỉ/SĐT lúc thanh toán + dọn CRUD phi lý ở admin + footer/banner

Yêu cầu trực tiếp: bắt buộc điền địa chỉ + SĐT người nhận trước khi thanh toán, admin phải có
chỗ xem rõ chi tiết đơn hàng. Kèm đọc tiếp `BUG.ipynb` (mục 4 mới).

### Địa chỉ nhận hàng + SĐT người nhận

- Thêm `Order.shipping_address` + `Order.recipient_phone` (migration `0003`).
- `orders/views.py::checkout()`: kiểm tra bắt buộc 2 trường này ở SERVER (không chỉ dựa
  `required` của HTML - người dùng có thể tắt JS bỏ qua), chặn với thông báo rõ ràng nếu thiếu.
- Modal thanh toán (`cart.html`): thêm 2 ô nhập TRƯỚC phần chọn hình thức thanh toán, tự điền
  sẵn từ `user.address`/`user.phone_number` nếu hồ sơ đã có (vẫn cho sửa/xác nhận lại per đơn).

### BUG.ipynb mục 4 - dọn CRUD phi lý ở admin

Đúng như người dùng chỉ ra: "Thêm vào Đánh giá sản phẩm" ở admin là sai logic (khách hàng mới
là người viết đánh giá, admin không có quyền bịa ra). Áp dụng NGUYÊN TẮC này rộng hơn, tự rà
thêm các model khác có cùng vấn đề (không chỉ Review):

- `Review`: bỏ quyền Thêm VÀ Sửa (`has_add/change_permission` trả `False`) - chỉ Xem (chỉ đọc)
  + Xóa (kiểm duyệt). Django tự đổi tiêu đề trang "...để thay đổi" → "...để xem" khi phát hiện
  không có quyền sửa (cơ chế có sẵn, không cần code thêm).
- `Order`: cũng bỏ Thêm/Sửa (đơn hàng là dữ liệu lịch sử, admin tự tạo/sửa sẽ sai lệch bằng
  chứng đã mua) + thêm cột `xem_chi_tiet` hiện link "Chi tiết đơn hàng →" rõ ràng trong danh
  sách (đúng yêu cầu "phải có chỗ click ghi chữ chi tiết đơn hàng").
- `Wallet`: bỏ Thêm (tự tạo qua signal, 1-1 với User) VÀ Sửa (đổi thẳng "balance" sẽ không khớp
  lịch sử giao dịch bên dưới). `Transaction`: bỏ Thêm/Sửa (phải bất biến để còn đối soát được).
- Sửa dòng chữ thống kê: "Thống kê cảm xúc (trên N đánh giá đang lọc/tìm): ..." → chỉ còn
  "Thống kê bình luận: ..." theo đúng yêu cầu.
- Đổi câu chữ banner trang chủ + đoạn giới thiệu ở footer (trước đó là văn mẫu thương mại điện
  tử chung chung, không nhắc gì đến kính mắt) sang đúng giọng điệu Astraea.

### ⚠️ Sự cố ngoài ý muốn tự gây ra và đã khắc phục ngay trong phiên

Lúc viết test kiểm tra validation địa chỉ/SĐT, đã dọn "các đơn hàng rỗng" bằng
`Order.objects.filter(shipping_address='').delete()` - QUÊN MẤT rằng `Review.order_item` có
`on_delete=CASCADE` lên `OrderItem` → `Order`, nên lệnh này CASCADE xóa theo TOÀN BỘ 45 đánh
giá đã seed (mất trắng, phát hiện qua việc box thống kê ở admin đột nhiên biến mất chứ không
báo lỗi gì). Đây là dữ liệu demo/seed (không phải dữ liệu người dùng thật) nên đã khôi phục
ngay bằng cách chạy lại `python manage.py seed_reviews` (idempotent, tự phát hiện thiếu và tạo
lại) - kết quả còn ĐẦY ĐỦ HƠN trước (60 đánh giá, phủ cả sản phẩm Dublin mới thêm sau này).
**Bài học**: trước khi xóa hàng loạt theo điều kiện, phải rà lại chuỗi `on_delete=CASCADE` của
MỌI model tham chiếu tới bảng đó, không chỉ nhìn 1 tầng quan hệ trực tiếp.

### Tự kiểm tra bằng luồng thật (POST + Playwright, không chỉ đọc code)

Test cả 2 nhánh: thiếu địa chỉ/SĐT → bị chặn đúng thông báo, KHÔNG tạo đơn (xác nhận trong
CSDL); đủ thông tin → đặt hàng thành công, lưu đúng địa chỉ/SĐT/hình thức thanh toán. Test
quyền admin bằng cách gọi thẳng URL `/add/` của Review/Order/Wallet/Transaction → cả 4 đều trả
403 đúng như mong đợi; xác nhận nút "Thêm" KHÔNG còn xuất hiện ở khu vực nút thao tác của trang
Review (không nhầm với link "Thêm vào" của app Favorite ở sidebar chung). Chụp ảnh xác nhận
trang "Xem Đơn hàng" hiện đúng địa chỉ/SĐT/danh sách sản phẩm, chỉ có nút Đóng/Xóa (không có
Lưu); trang chủ hiện đúng banner + footer mới.

---

## 40. NHẬT KÝ PHIÊN LÀM VIỆC — Đổi theme Django admin sang xanh navy-trắng

Django admin (4.2) tự theme qua CSS custom properties khai báo ở `:root` trong
`base.css`/`dark_mode.css` gốc - không cần sửa file của Django, chỉ cần NẠP THÊM 1 file CSS
ghi đè các biến đó SAU file gốc (thứ tự nạp sau tự thắng, không cần `!important`).

- `static/css/admin-theme.css`: ghi đè `--primary`/`--secondary`/`--accent`/`--button-bg`... 
  sang bảng màu navy đậm + xanh dương (khớp `:root` của `style.css` site chính). Ép luôn
  `html[data-theme="dark"]` dùng chung 1 bảng màu sáng duy nhất (đồ án không cần hỗ trợ
  light/dark riêng cho trang admin).
- `templates/admin/base_site.html` (override `admin/base_site.html` gốc, chỉ thêm
  `{% block extrastyle %}` nạp file CSS trên) - không đụng gì khác của Django admin.
- `core/urls.py`: đặt `admin.site.site_header/site_title/index_title` = "Astraea..." để tên
  thương hiệu hiện đúng ở tiêu đề tab, đầu trang, trang chủ admin.

**Tự kiểm tra bằng ảnh chụp thật** (Playwright + Edge, đăng nhập admin thật): trang chủ admin,
danh sách sản phẩm, form thêm sản phẩm - cả 3 đều nhất quán navy đậm (header/breadcrumb/tiêu đề
mục) + trắng (nền nội dung) + xanh dương (link, nút CTA), khớp đúng thương hiệu Astraea.

---

## 39. NHẬT KÝ PHIÊN LÀM VIỆC — Kiểm tra CRUD trong trang admin

Yêu cầu: "kiểm tra thao tác crud trong admin phải khớp, chính xác, loại bỏ mục dư thừa".

- **Loại bỏ mục dư thừa**: `admin.site.unregister(Group)` trong `accounts/admin.py` - model
  "Nhóm" (phân quyền theo nhóm) mặc định của Django nhưng dự án này KHÔNG dùng tới ở bất kỳ đâu
  (chỉ phân quyền qua `is_staff`/`is_superuser`), grep toàn bộ code xác nhận trước khi xóa -
  trước đây hiện 1 mục trống không ai dùng trong "XÁC THỰC VÀ ỦY QUYỀN".
- **Kiểm tra CRUD thật** (POST request thật qua `requests`, không phải đọc code suông): đăng
  nhập admin → tạo mới, xem, sửa, xóa thử 1 `Category` VÀ 1 `Product` (có cả FK danh mục +
  inline `ProductImage` formset - phần phức tạp nhất) → xác nhận từng bước bằng cách đọc thẳng
  giá trị trong CSDL sau mỗi thao tác (không chỉ nhìn HTML trả về, tránh bị đánh lừa bởi cache
  hay định dạng hiển thị khác biệt). Cả 2 đều CRUD đúng hoàn toàn; đã xóa sạch dữ liệu test sau
  khi kiểm xong.
- Smoke-test 10/10 trang danh sách (changelist) của mọi model đã đăng ký admin - tất cả trả về
  HTTP 200, không có trang nào lỗi 500 do `list_display`/`list_filter` tham chiếu sai field.

**Sự cố phát hiện rồi tự bác bỏ trong lúc test** (đáng ghi lại để không lặp lại nhầm lẫn): lúc
đầu nghi có lỗi redirect ở trang đăng nhập GỐC của Django (`/admin/login/`) - test bằng `curl`
thấy đăng nhập xong lại về trang chủ thay vì `/admin/`. Đã đào sâu vào tận source code
`django.contrib.auth.views.LoginView` và `AdminSite.login()` để hiểu cơ chế `next`, rồi xác
minh lại bằng 2 công cụ độc lập khác (`Client` test của Django và thư viện `requests` của
Python) - cả hai đều cho kết quả ĐÚNG (`/admin/`). Kết luận: đây là lỗi trong chính cách gọi
`curl` lúc test (không phải lỗi ứng dụng) - không sửa gì cả, tránh "sửa" nhầm một thứ vốn không
hề hỏng.

---

## 38. NHẬT KÝ PHIÊN LÀM VIỆC — Dọn dữ liệu kính thừa trong seed_products.sql

Yêu cầu: "xóa sql database dữ liệu kính thừa trong file seed". Đối chiếu file với CSDL thật:
file gốc có 10 danh mục + ~45 dòng `INSERT INTO products_product`, nhưng CSDL thật (kiểm tra
trực tiếp) chỉ có ĐÚNG 2 danh mục (`vuong-square`, `oval`) và 4 sản phẩm thật (Incantation,
Mythic, Impossible, Dublin) - toàn bộ ~42 sản phẩm còn lại (Dirty Magic, Numero Seis, Freigeist,
Bubbles...) tham chiếu tới file ảnh KHÔNG hề tồn tại trong `media/products/` và chưa từng được
chèn vào CSDL - đây chính là "dữ liệu thừa" (rác crawl còn sót, chưa từng thực sự lên web).

Đã viết lại `seed_products.sql` từ 250 dòng xuống còn 41 dòng: chỉ giữ 2 danh mục và 4 sản phẩm
thật đang có trên web (thêm cả `Dublin` - sản phẩm Oval mới tạo ở mục 37 - vào seed luôn, dùng
đúng nội dung/thông số/mô tả đã lưu trong CSDL, để file phản ánh đúng catalogue thật hiện tại).

**Tự kiểm tra** (không chỉ đọc code): chạy thẳng file mới lên CSDL thật qua `mysql < seed_products.sql`
- không lỗi cú pháp, không tạo trùng lặp (vẫn đúng 4 sản phẩm/2 danh mục nhờ `WHERE NOT EXISTS`).
Kiểm tra kỹ hơn phần JSON `specs` của Dublin (không thể test qua đường "đã tồn tại thì bỏ qua"
vì dòng đó vốn đã có sẵn) bằng cách chạy INSERT đó thật trong 1 transaction có `ROLLBACK` - xác
nhận MySQL báo `JSON_VALID = 1` và không để lại dấu vết gì trên dữ liệu thật sau khi rollback.

---

## 37. NHẬT KÝ PHIÊN LÀM VIỆC — "Lỗi 3" trong BUG.ipynb + sản phẩm Oval từ carfia.com

Người dùng bổ sung tiếp nội dung mới vào `BUG.ipynb` ("3. bỏ dòng này đi..."), yêu cầu đọc kỹ
rồi làm, có 4 việc:

1. **Bỏ dòng trust-strip ở trang chủ** ("Miễn phí vận chuyển/Thanh toán an toàn/Đổi trả dễ
   dàng/Hỗ trợ 24/7" ngay dưới hero) - xóa hẳn section + toàn bộ CSS liên quan không còn dùng
   (`.trust-strip`, `.trust-item`, `.trust-icon` và 2 rule responsive). Dòng "Bảo mật qua ví
   điện tử" trong đó cũng không còn đúng nữa từ khi đổi sang thanh toán giả lập.
2. **Nhãn cảm xúc từng bình luận đổi thành CÔNG KHAI** (trước đó chỉ tác giả + admin thấy, xem
   mục 34) - người dùng xem lại và muốn MỌI người đều thấy nhãn Tích cực/Trung lập/Tiêu cực
   ngay trên từng bình luận (khác với % tổng hợp cả sản phẩm). Đã bỏ điều kiện
   `is_staff`/`review.user` ở template, nhãn giờ hiện cho tất cả.
3. **Modal thanh toán giả lập "bị lỗi" - bấm không ra popup chọn MoMo/Thẻ/COD**: đọc lại code
   không thấy lỗi logic, nghi ngay do cùng nguyên nhân đã gặp với CSS (cache trình duyệt) -
   nhưng lần này là `main.js` (chứa `initPaymentModal`) và `review-form.js`, cả hai đều CHƯA có
   `?v=` chống cache như `style.css` đã có từ mục 34. Đã thêm `?v=2` cho cả 2 file JS.
   **Tự kiểm tra bằng click THẬT** (không chỉ đọc code): cài Playwright, dùng lại Edge có sẵn
   trong máy (`channel="msedge"`, không cần tải trình duyệt mới) để bấm nút "Thanh toán" thật -
   xác nhận modal mở đúng (chụp ảnh có đủ 3 lựa chọn COD/MoMo/Thẻ), chọn "Ví MoMo" bấm "Xác nhận
   thanh toán" → đặt hàng thành công thật (đơn #52).
4. **Sản phẩm kính Oval từ carfia.com**: dùng endpoint JSON Shopify
   (`carfia.com/products/dublin-ca5506fc10.json`, cùng kỹ thuật đã dùng với lespecs.com) lấy
   đúng thông số + toàn bộ URL ảnh gốc. Đã xem trực tiếp từng ảnh trước khi tải: ảnh
   front/side/detail/angle đúng là ảnh sản phẩm thuần (nền trắng, không người) - GIỮ; ảnh gắn
   nhãn "lifestyle" hóa ra lại là ảnh người mẫu đeo kính (nhìn bằng mắt mới phát hiện, tên file
   gây hiểu lầm) - LOẠI theo đúng yêu cầu "không lấy ảnh người mẫu"; ảnh "model" và "size-chart"
   loại luôn (người mẫu / thông số). Tạo `Product` mới "Dublin" (danh mục Oval, giá 1.890.000đ,
   unisex, SKU giữ nguyên `CA5506-FC10`) với mô tả + bullet + thông số kỹ thuật tự viết bằng
   tiếng Việt (theo đúng "bạn tự bịa ra cũng được"), 1 ảnh chính + 3 ảnh gallery.

### Tự kiểm tra bằng ảnh chụp thật

Trang chủ: trust-strip đã biến mất, "Oval" ở danh mục nổi bật giờ hiện đúng ảnh kính Dublin
thật (trước đó chỉ có chữ "O" vì chưa có sản phẩm nào). Trang sản phẩm Dublin: đủ 4 ảnh, giá/
thông số/mô tả/hướng dẫn bảo quản hiển thị đúng, nút "Thêm vào giỏ hàng" đúng kích thước (không
còn lỗi phồng to đã sửa ở mục 36). Nhãn cảm xúc: `curl` KHÔNG kèm cookie đăng nhập vẫn thấy
nhãn "Tiêu cực" trên bình luận - xác nhận đã công khai đúng yêu cầu mới.

### Tự kiểm tra bằng luồng thật (curl, không chỉ đọc code)

Xác nhận không còn `{#` lộ ra (grep toàn bộ `templates/`); nút giỏ hàng nhanh trang chủ submit
thành công (thêm đúng sản phẩm); đăng nhập `admin` → redirect đúng `/admin/`; đăng nhập `Minh`
(không phải staff) → vẫn về trang chủ như cũ; thêm giỏ hàng → mở modal thanh toán chọn "MoMo" →
đặt hàng thành công **mà ví KHÔNG bị trừ** (số dư trước/sau giống hệt nhau, đã kiểm tra trong
MySQL) → đơn hàng lưu đúng `payment_method=MOMO`; biểu đồ admin trả về đúng % khớp với số liệu
đã biết trước đó (Incantation 56/6/38, tổng 100%).

---

## 38. GIAI ĐOẠN 3 — TỐI ƯU ĐỘ TRỄ THỬ KÍNH ẢO (Bài toán A, mục 11)

Người dùng nhờ đọc file đánh giá độc lập `danh_gia_cam_xuc_va_kinh_ao.txt` (do người dùng tự
viết/tổng hợp, không phải do phiên trước tạo) - file này xác nhận: Giai đoạn 3 (5 kỹ thuật tối
ưu độ trễ đã lên kế hoạch từ mục 11) **CHƯA từng được áp dụng vào bản web** (chỉ mới cache PNG
kính - 1/5), và **CHƯA từng đo FPS/độ trễ trên chính pipeline WebSocket thật** (trước đó chỉ có
baseline 26,96 FPS đo trên `prototype/tryon_demo.py` chạy độc lập, không qua Django/WebSocket).
Người dùng đồng ý bắt đầu triển khai Giai đoạn 3.

### Phát hiện thêm trước khi tối ưu: debug logging cũ tự gây thêm độ trễ

Rà lại `tryon/consumers.py` + `static/js/tryon.js` phát hiện cơ chế debug tạm (từ phiên
debug-mode trước, dò lỗi H1-H4 camera/modal - các lỗi đó đã được xác nhận sửa xong ở mục 27-29)
**vẫn còn chạy trên MỌI khung hình**: phía client `debugLog()` gọi `fetch("/__debug_log__/")`
(1 HTTP request riêng) mỗi khi nhận 1 khung phản hồi; phía server `_debug_log()` mở + ghi + đóng
file `.claude/debug.log` mỗi khung trong `_process_frame_sync` (đường CPU nóng nhất). Đây là I/O
thực tế trên mọi khung hình, ngược hẳn với mục tiêu "giảm độ trễ" của giai đoạn này - đã xóa
toàn bộ (file `tryon/debug_log.py`, route `__debug_log__/` trong `core/urls.py`, mọi lời gọi
`debugLog(...)` trong `tryon.js`) trước khi đo baseline, vì để lại sẽ làm baseline/kết quả đo bị
sai lệch bởi chi phí I/O không liên quan tới thuật toán.

### 5 kỹ thuật đã áp dụng vào `tryon/consumers.py` + `tryon/vision.py`

1. **Thu nhỏ ảnh trước khi đưa vào MediaPipe** (`DETECT_DOWNSCALE_WIDTH = 400px`) khi CHƯA có vị
   trí mặt từ khung trước - luôn vẽ/dán kính lên khung hình GỐC (không bị thu nhỏ). Landmark
   MediaPipe là toạ độ chuẩn hoá (0..1) nên độc lập với độ phân giải ảnh đưa vào -
   `FaceMeshDetector.get_eye_anchor_points` thêm tham số `region_offset` để ánh xạ đúng toạ độ
   pixel trong khung gốc bất kể đã resize/cắt vùng nào.
2. **Giới hạn tần suất gọi `detect()` ~15 lần/giây** (`MIN_DETECT_INTERVAL_MS`), CHỈ khi đang bám
   vết ổn định (`_last_face_box` khác `None`) - giữa 2 lần detect thật, tái dùng toạ độ neo thô
   của lần gần nhất (vẫn được đưa qua bộ lọc mượt mỗi khung, không "đứng hình").
3. **One-Euro filter** (`AnchorSmoother`, lớp mới trong `tryon/vision.py`) làm mượt tâm/bề
   rộng/góc của 2 điểm neo mắt trước khi vẽ kính - chống rung do nhiễu nhận diện từng khung.
   Reset khi mất mặt để tránh kính "trượt" từ vị trí cũ khi tìm lại được mặt.
4. Cache renderer theo `glasses_id` - đã có từ trước Giai đoạn 3, giữ nguyên (không đọc lại PNG
   mỗi khung).
5. **ROI quanh mắt + CLAHE có điều kiện**: khi đã có vị trí mặt từ khung trước, chỉ cắt + resize
   vùng ROI quanh mặt (`ROI_DETECT_SIZE = 256px`, cạnh = `eye_distance * ROI_PADDING_RATIO`) đưa
   vào MediaPipe thay vì cả khung hình; và CLAHE (`LightNormalizer.normalize`) chỉ chạy khi
   `is_low_light()` thực sự báo thiếu sáng (hàm này có sẵn từ đầu nhưng chưa bao giờ được dùng để
   bật/tắt - đúng như file đánh giá đã chỉ ra).

### Đo FPS trước/sau — LẦN ĐẦU đo trên chính pipeline xử lý thật (không phải prototype)

Không dùng `channels.testing.WebsocketCommunicator` được (treo không rõ nguyên nhân khi gọi qua
lớp Channels/ASGI - nghi thread-affinity của MediaPipe VIDEO-mode qua thread pool của
`sync_to_async`, chưa kết luận chắc vì không phải mục tiêu của giai đoạn này). Thay vào đó gọi
**trực tiếp** `TryOnConsumer._process_frame_sync` (đúng hàm thật trong code, không viết lại logic
riêng) với 1 khung hình có mặt người thật (crop từ `media/avatars/4.jpg`, ảnh do người dùng có
sẵn trong máy - đã xác nhận MediaPipe nhận diện được mặt trong crop này), lặp 120 khung, đo qua
`time.perf_counter()` - script tại `scripts/bench_tryon_direct.py` (tạm, trong scratchpad).

| Cấu hình | FPS | Trung bình/khung |
|---|---|---|
| Baseline (code TRƯỚC Giai đoạn 3, đo trực tiếp) | 33,3 | 30,0 ms |
| Sau khi áp dụng ĐỦ 5 kỹ thuật | 54,4 | 18,4 ms |

**Bảng đối chiếu từng kỹ thuật riêng lẻ** (tắt lần lượt 1 kỹ thuật khỏi bản đã tối ưu, script
`bench_tryon_ablation.py`, cùng máy/cùng ảnh test, 120 khung/cấu hình):

| Cấu hình | FPS | So với FULL |
|---|---|---|
| FULL (5/5 kỹ thuật) | 53,5 | - |
| Tắt kỹ thuật 3 (bỏ smoothing) | 54,9 | +1,4 (nhiễu đo, xem giải thích) |
| Tắt kỹ thuật 5a (CLAHE luôn chạy, bỏ `is_low_light` gating) | 47,1 | −6,4 |
| Tắt phần giảm độ phân giải của kỹ thuật 5 (ROI vẫn khoanh vùng, không resize nhỏ) | 52,3 | −1,3 |
| Tắt kỹ thuật 2 (detect() mỗi khung, vẫn có ROI) | 38,3 | −15,3 |
| Tắt kỹ thuật 1+2+5 (detect() mỗi khung, full-frame, giống trước GĐ3) | 37,5 | −16,0 |
| Tắt cả 4 kỹ thuật có thể tắt (đối chiếu sanity-check với baseline gốc) | 36,0 | ≈ baseline 33,3 (chênh do nhiễu hệ thống) |

**Nhận xét quan trọng cho báo cáo** (rút ra từ chính số liệu, không suy đoán):
- **Kỹ thuật 2 (giảm tần suất gọi `detect()`) đóng góp lớn nhất**, không phải kỹ thuật giảm độ
  phân giải (1/5b) như dự đoán ban đầu trong kế hoạch. Lý do: `FaceLandmarker` của MediaPipe có
  chi phí gần như CỐ ĐỊNH mỗi lần gọi (mô hình tự chuẩn hoá kích thước đầu vào nội bộ), nên GIẢM
  SỐ LẦN GỌI tác động nhiều hơn giảm SỐ PIXEL mỗi lần gọi trong trường hợp webcam 640×480 này.
- **Kỹ thuật 5a (CLAHE có điều kiện)** là đóng góp lớn thứ hai - đúng như file đánh giá đã chỉ ra
  đây là chỗ hở rõ nhất (hàm `is_low_light()` có sẵn nhưng chưa từng được dùng).
- **Kỹ thuật 3 (One-Euro filter) KHÔNG làm tăng FPS** (chênh lệch trong khoảng nhiễu đo) - đúng
  bản chất của nó: mục tiêu là giảm CẢM GIÁC rung/trễ ở CÙNG một FPS (làm mượt chuyển động), không
  phải tăng tốc xử lý. Cần nêu rõ điều này khi báo cáo để không bị hỏi ngược "sao áp dụng kỹ thuật
  3 mà FPS không tăng".
- Kỹ thuật 4 (cache PNG) không đo lại được công bằng trong 1 phiên vì renderer chỉ tạo 1 lần lúc
  khởi tạo script - giá trị của nó là giảm độ trễ của riêng hành động "đổi kính" (vài chục ms/lần
  đổi), không phải FPS ổn định liên tục.
- Số đo dùng `_process_frame_sync` trực tiếp, **bỏ qua lớp Channels/ASGI/WebSocket** (không phải
  mục tiêu tối ưu của giai đoạn này) - tức là chưa tính độ trễ mạng trình duyệt↔server, vốn phụ
  thuộc phần cứng/mạng người dùng thật, không phải chi phí CPU mà 5 kỹ thuật này nhằm vào.

### Đã dọn dẹp

- Xóa `tryon/debug_log.py`, route `__debug_log__/` trong `core/urls.py`, toàn bộ `debugLog(...)`
  trong `static/js/tryon.js` (xem phần "Phát hiện thêm" ở trên).
- Cập nhật docstring đầu `tryon/consumers.py`/`tryon/vision.py` mô tả đúng 5 kỹ thuật đã áp dụng
  và lý do (để phiên sau không phải đọc lại toàn bộ diff mới hiểu).

### Chưa làm / cần làm nếu muốn đầy đủ hơn

- Chưa đo trên **bản web thật qua trình duyệt** (webcam thật, mạng thật, nhiều lần đổi kính) -
  chỉ đo được pipeline CPU nội bộ như trên. Nếu cần số liệu "cảm nhận thực tế" cho báo cáo, nên tự
  mở trang thử kính, quan sát log console server (`[TryOn][GiaiDoan3] FPS~=... avg_process_ms=...`
  - dòng này tự in ra mỗi 5 giây, xem `FPS_LOG_INTERVAL_S` trong `tryon/consumers.py`) trong lúc
  dùng thật, rồi so với bảng trên.
- Nguyên nhân `channels.testing.WebsocketCommunicator` bị treo khi test qua lớp Channels chưa
  được điều tra tới cùng - có thể chỉ là quirk của bộ test harness, nhưng cũng có thể liên quan
  tới việc gọi `FaceMeshDetector.detect()` (giữ trạng thái VIDEO-mode) từ các thread khác nhau của
  thread pool `sync_to_async(..., thread_sensitive=False)`. Không ảnh hưởng tới việc đo/tối ưu vừa
  làm (đã tránh bằng cách gọi trực tiếp), nhưng nếu sau này thấy treo/lag bất thường trong sản
  xuất thật khi nhiều người dùng cùng lúc, đây là nơi đầu tiên nên nghi.

---

## 39. SỬA LỖI "GIẬT/NHẤP NHÁY LIÊN TỤC" khi test Giai đoạn 3 trên web thật

Người dùng tự mở trang thử kính qua trình duyệt thật (theo hướng dẫn ở mục 38) và báo: "khi bật
webcam lên thì nó giật liên tục, không ổn định, nhấp nháy liên tục" - yêu cầu tìm nguyên nhân và
sửa, có tính toán cụ thể (không chỉ sửa mò). Đây là lần ĐẦU TIÊN tính năng được test qua webcam
thật kể từ khi làm Giai đoạn 3 (mục 38 chỉ đo FPS bằng ảnh tĩnh lặp lại, không phát hiện được các
lỗi này). Đã tìm ra và XÁC NHẬN BẰNG SỐ ĐO 2 nguyên nhân cụ thể (không suy đoán):

### Nguyên nhân 1 — One-Euro filter (kỹ thuật 3) gần như KHÔNG hoạt động

**Cách phát hiện**: gửi LẶP LẠI đúng 1 khung hình (ảnh không đổi) 40 lần liên tiếp qua
`_process_frame_sync` thật. Nếu ảnh không đổi, vị trí mắt phải đứng yên - nhưng đo ra vị trí THÔ
(trước lọc) nhảy 137,9 → **111,1** → 136,9 → 140,5 → 141,5 (dao động ±19% dù đầu vào giống hệt -
đây là nhiễu nội tại của chính bộ theo dõi VIDEO-mode của MediaPipe, không phải lỗi code). Đo tiếp
độ lệch chuẩn SAU khi qua `AnchorSmoother`: ~5,28 - GẦN BẰNG HOẶC CAO HƠN nhiễu thô (~4,7) - tức bộ
lọc coi như vô dụng.

**Tính toán nguyên nhân**: `beta` của One-Euro filter nhân trực tiếp với VẬN TỐC tín hiệu. Tín
hiệu ở đây đo bằng PIXEL (không phải toạ độ chuẩn hoá 0..1 như bài báo gốc dùng), nên vận tốc lớn
hơn nhiều bậc độ lớn. Với bước nhảy nhiễu ~27px/0,08s ≈ 335px/s và `beta=0,4` (giá trị copy từ ví
dụ phổ biến, KHÔNG đổi tỉ lệ cho đơn vị pixel): `cutoff = min_cutoff + beta×|vận tốc| = 1,0 +
0,4×335 ≈ 135` - cutoff bị đội lên gấp ~135 lần, làm bộ lọc hầu như không còn lọc gì (tương đương
gần như dùng thẳng giá trị thô).

**Đã sửa**: đo thử lại nhiều bộ tham số trên đúng chuỗi nhiễu đã ghi được (xem
`tryon/vision.py::OneEuroFilter`/`AnchorSmoother` docstring có ghi lại số liệu so sánh) - chọn
`min_cutoff=0,5, beta=0,015` (giảm ~2000% so với 0,4 cũ): giảm độ lệch chuẩn nhiễu xuống ~3,66-3,99
(giảm 15-30% tuỳ chuỗi dữ liệu) mà độ trễ khi đầu quay THẬT (mô phỏng dịch 40px/0,24s) chỉ chậm
~1 khung (~80ms) so với tín hiệu thật - dưới ngưỡng nhận biết của mắt người. Thử `beta=0` (tắt hẳn
thích nghi) giảm nhiễu mạnh nhất (~60%) nhưng làm kính trễ rõ so với đầu quay thật - không chọn vì
đánh đổi không đáng.

### Nguyên nhân 2 — CLAHE tự bật/tắt gây nhấp nháy CẢ khung hình

**Cách phát hiện + tính toán**: kỹ thuật 5 ở mục 38 dùng `is_low_light()` - 1 ngưỡng CỨNG (90) để
quyết định chạy CLAHE hay không mỗi khung. Mô phỏng đúng kiểu nhiễu độ sáng tự nhiên của webcam
(dao động ±2-4 đơn vị quanh một mức nền, ví dụ chuỗi 92,88,91,87,93,89,90,86,94,88,91,89,92 - đều
là dao động rất nhỏ, hoàn toàn có thể xảy ra do auto-exposure) rồi gọi `is_low_light()` liên tiếp:
kết quả đổi trạng thái **12/12 lần** - tức là CLAHE bật/tắt ở **MỌI khung hình liên tiếp**. Vì ảnh
có CLAHE và không có CLAHE khác nhau rõ về độ sáng/tương phản, việc bật/tắt mỗi khung tạo ra đúng
hiệu ứng "cả hình ảnh nhấp nháy" mà người dùng mô tả - đây là lỗi kinh điển "bang-bang oscillation"
khi dùng 1 ngưỡng cứng cho tín hiệu có nhiễu.

**Đã sửa**: thêm `LightNormalizer.should_normalize()` (xem `tryon/vision.py`) - dùng HYSTERESIS
(2 ngưỡng cách nhau `hysteresis=12` đơn vị quanh ngưỡng 90: vào chế độ tối khi <84, ra khi >96) +
trạng thái DÍNH (sticky) giữa các khung - ở khoảng giữa 2 ngưỡng thì giữ nguyên trạng thái cũ. Test
lại CHÍNH chuỗi nhiễu trên: **0/12 lần đổi trạng thái** (từ 12 xuống 0). `tryon/consumers.py` đổi
gọi `is_low_light()` → `should_normalize()`.

### Cải thiện phòng ngừa thêm (không đo được trực tiếp do giới hạn môi trường, nhưng có cơ sở)

Thêm `MAX_CONSECUTIVE_MISSES = 3`: trước đây 1 lần `detect()` không ra kết quả (có thể do ROI quá
hẹp/nhiễu tức thời) làm xoá NGAY `_last_face_box`/`_last_raw_anchors` → kính biến mất rồi hiện lại
ngay khung sau nếu khung kế tiếp detect lại được → cảm giác nhấp nháy. Giờ chỉ thực sự coi là mất
mặt sau 3 lần LIÊN TIẾP không ra kết quả; trong lúc "dung sai" đó kính giữ nguyên vị trí cũ (đứng
yên) thay vì biến mất. Không có webcam thật trong môi trường này nên không đo trực tiếp được tần
suất miss thật của người dùng - đây là cải thiện phòng ngừa dựa trên suy luận hợp lý, cần người
dùng xác nhận lại có còn thấy hiện tượng biến-mất-rồi-hiện-lại không.

### Đã kiểm tra không hồi quy (regression)

Chạy lại `scripts/bench_tryon_direct.py` sau khi sửa: FPS ~52,6 (so với ~54,4 trước khi sửa mục
này) - KHÔNG giảm đáng kể (chênh lệch trong khoảng nhiễu đo giữa các lần chạy), xác nhận 3 chỗ sửa
trên chỉ thay đổi THAM SỐ/ĐIỀU KIỆN, không thêm chi phí CPU đáng kể nào.

### Chưa làm / giới hạn

- KHÔNG có webcam thật trong môi trường chạy Claude Code này, nên không thể tự xem trực tiếp hiệu
  ứng đã hết giật/nhấp nháy chưa - mọi con số ở trên đo bằng cách gọi thẳng hàm xử lý với ảnh tĩnh/
  dữ liệu mô phỏng, KHÔNG phải quan sát bằng mắt trên webcam thật. Người dùng cần tự mở lại trang
  thử kính, xác nhận cảm giác thực tế, và nếu vẫn còn hiện tượng lạ thì mô tả CHI TIẾT HƠN (nhấp
  nháy là cả hình ảnh sáng/tối đổi, hay chỉ riêng kính biến mất/lệch vị trí, hay hình bị đứng khung
  rồi nhảy cóc) để khoanh vùng đúng nguyên nhân còn lại nếu có.

---

## 40. SỬA LỖI "NHẬN DẠNG KÍNH LÊN MẶT HƠI LÂU" — cold-start MediaPipe mỗi kết nối

Người dùng test lại trên web thật (sau mục 39), báo độ trễ vẫn còn, cụ thể là **lúc mới bật
webcam, việc dán kính lên mặt hơi lâu** (không phải giật liên tục như mục 39 nữa - đây là 1 dạng
độ trễ KHÁC: chậm ở lần đầu, không phải chậm liên tục).

### Nguyên nhân — đo trực tiếp, không suy đoán

Đo thời gian tạo `FaceMeshDetector` (bọc `mediapipe.tasks.python.vision.FaceLandmarker`) - đây là
việc `connect()` trong `tryon/consumers.py` làm cho MỌI kết nối WebSocket mới:

| Lần tạo trong 1 tiến trình Python | Thời gian |
|---|---|
| Lần 1 (đầu tiên trong tiến trình) | **~3.000 - 5.900 ms** |
| Lần 2, 3... (cùng tiến trình) | **~25 ms** (nhanh hơn ~100-200 lần) |

Đây là chi phí **1 LẦN CHO CẢ TIẾN TRÌNH** (MediaPipe/TFLite/XNNPACK tự khởi tạo kernel tính toán +
nạp graph mô hình lúc lần đầu được gọi trong tiến trình, không phải chi phí riêng của từng
instance) - đã kiểm chứng bằng cách tạo lại trên thread khác, qua `sync_to_async` giống hệt code
thật... đều nhanh SAU KHI tiến trình đã "ấm" (warm). Vấn đề: trước đây, KHÁCH HÀNG ĐẦU TIÊN kết nối
sau MỖI LẦN server khởi động/tự nạp lại (autoreload - xảy ra mỗi khi sửa 1 file `.py`, tức là RẤT
THƯỜNG XUYÊN trong lúc phát triển) chính là người phải "trả" chi phí 3-6 giây này - đúng khớp với
mô tả "nhận dạng kính lên mặt hơi lâu".

### Đã sửa

Thêm `tryon/apps.py::TryonConfig.ready()` - khi server khởi động bằng `runserver` (bỏ qua các lệnh
khác như `migrate`/`makemigrations`/`shell` vì không cần), tạo 1 `FaceMeshDetector` "vứt đi" (tạo
xong đóng ngay) trong 1 thread nền NGAY LÚC SERVER KHỞI ĐỘNG - để chi phí 3-6 giây đó xảy ra 1 LẦN,
lúc chưa ai mở trang web, thay vì rơi vào kết nối thật của người dùng. Có canh để không chạy 2 lần
ở tiến trình "watcher" của autoreload (kiểm tra `RUN_MAIN`/`--noreload`).

### Xác minh bằng test WebSocket THẬT (qua mạng, không chỉ gọi hàm Python)

Cài tạm gói `websockets` (gỡ ra sau khi test xong, không đưa vào requirements.txt), viết script nối
thật tới `ws://127.0.0.1:8001/ws/tryon/` đang chạy, đo round-trip từng khung:

- **Lần đo đầu tiên** (vô tình có ~10 tiến trình Python cũ từ các bước test trước đó vẫn còn sống,
  tranh CPU - xem phần "Bài học" dưới đây): khung đầu tiên mất **5.627 ms** - SAI LỆCH do môi
  trường, không phải do code.
- **Sau khi dọn sạch tiến trình rác, khởi động lại server sạch sẽ**: khung đầu tiên chỉ **44 ms**,
  các khung sau 16-26 ms - nhanh ngay từ đầu, không còn độ trễ khởi động.

### Bài học phụ (vệ sinh môi trường test)

Trong lúc điều tra, phát hiện có ~10 tiến trình `python.exe` "rác" còn sống trên máy - nhiều khả
năng là hậu quả của các script chẩn đoán ngắn đã chạy trong các bước trước (mỗi lần tạo
`FaceMeshDetector` để test có thể để lại thread nền của MediaPipe không tự thoát, làm tiến trình
Python không kết thúc hẳn dù script đã chạy xong). Các tiến trình này tranh CPU khiến 1 lần đo bị
sai lệch nghiêm trọng (5,6 giây dù code đã đúng) - đã dọn sạch bằng `taskkill`. Đây không phải lỗi
của code sản phẩm, chỉ là hậu quả của cách tự test trong phiên làm việc này - không ảnh hưởng tới
người dùng thật khi họ tự chạy `runserver` một lần và dùng bình thường.

### Đã cập nhật cache-busting

`templates/products/detail.html` - đổi `tryon.js?v=2` → `?v=3` (đã sửa `tryon.js` ở mục 38 để bỏ
debug logging, nhưng số cache-busting chưa đổi nên trình duyệt có thể vẫn dùng bản JS cache cũ -
tuy về mặt hành vi bản cũ vẫn hoạt động đúng như nhau, nhưng bump số để chắc chắn khớp code mới).

---

## 41. THÊM KÍNH "DUBLIN" + GIẢM ĐỘ TRỄ CẢM NHẬN (tận dụng tốc độ server đã tối ưu)

Người dùng tự chỉnh sửa ảnh kính "Dublin" (sản phẩm Oval, mục 37) và bỏ file `Dublin.png` vào
`media/tryon/glasses/`, nhờ tích hợp vào thử kính ảo + tối ưu thêm độ trễ/giật.

### Tích hợp Dublin vào thử kính ảo

Kiểm tra `Dublin.png` (6000×3375, do người dùng cung cấp): **KHÔNG có kênh alpha** (3 kênh BGR
thường, nền trắng thuần) - `GlassesOverlay.__init__` bắt buộc PNG RGBA nên không dùng thẳng được
(sẽ báo lỗi, rơi về kính vẽ demo xấu xí). Đã tự tách nền:

- Phân tích histogram độ sáng: nền là trắng THUẦN (255), gọng kính nằm gọn trong khoảng 198-221 -
  có khoảng trống rõ (222-251 gần như không có pixel) nên ngưỡng mềm 225-245 tách sạch, không cần
  công cụ AI tách nền ngoài (ảnh nền trắng đơn giản, đủ điều kiện dùng ngưỡng độ sáng).
- Lưu thành `Dublin_f.png` (đúng quy ước hậu tố "_f" như 2 mẫu có sẵn Jasmin/Vanta). File gốc
  `Dublin.png` (chưa tách nền) GIỮ NGUYÊN, không xoá.
- Kiểm tra `GlassesOverlay._find_lens_anchors` tự tìm ĐÚNG 2 tâm tròng kính (chế độ TỰ ĐỘNG hoạt
  động, không cần chỉnh `width_ratio`/`vertical_offset` thủ công) - 2 tâm đối xứng qua trung tâm
  ảnh (lệch trục Y chỉ ~0.2px, cách đều tâm ~660px mỗi bên).
- Render thử lên ảnh mặt test (`media/avatars/4.jpg`) bằng `render_on_frame_auto` thật - kính bám
  đúng vị trí, xoay đúng theo góc nghiêng đầu.
- Thêm migration `tryon/migrations/0003_seed_dublin_glasses.py` (theo đúng khuôn mẫu migration
  0002 đã có) gắn `GlassesOverlay` cho sản phẩm slug `dublin` (pk=72) → `Dublin_f.png`. Chạy
  `migrate tryon` thành công, `makemigrations --check --dry-run` sạch.
- **Kiểm tra bằng WebSocket THẬT** (không chỉ gọi hàm): `curl` xác nhận trang `/san-pham/dublin/`
  đã hiện nút "Thử kính ảo" (`data-glasses-id="3"`) và gallery đủ 3 mẫu; gửi khung hình test qua
  `ws://.../ws/tryon/` với `glasses_id=3` → nhận về đúng ảnh có dán kính Dublin.

### Giảm độ trễ cảm nhận thêm - phát hiện điểm nghẽn MỚI sau khi đã tối ưu server

Người dùng báo "vẫn còn độ trễ nhận kính" sau các lần sửa mục 38-40. Đo lại bằng WebSocket thật
(giống mục 40): server ổn định ở **~18-35ms/khung** sau khi warm-up xong. NHƯNG `static/js/tryon.js`
giới hạn cứng client chỉ gửi tối đa **1 khung mỗi 80ms (12,5 fps)** - giá trị này được chọn TỪ TRƯỚC
Giai đoạn 3, lúc server còn xử lý ~30ms/khung chưa tối ưu gì. Sau khi tối ưu, **client hiện là điểm
nghẽn chính**: dù server có thể trả lời nhanh hơn nhiều, người dùng vẫn chỉ thấy tối đa 12,5 khung
hình/giây vì chính trình duyệt tự chặn không gửi thêm.

**Đã sửa**: giảm `CAPTURE_INTERVAL_MS` từ 80 xuống **40ms** (~25 fps trần) trong `static/js/tryon.js`
- vẫn còn dư biên an toàn so với ~18-35ms server cần, và cơ chế `waitingForResponse` (đã có sẵn,
không đổi) vẫn đảm bảo không bao giờ gửi dồn ứ nếu mạng/máy người dùng chậm hơn dự kiến. Đồng thời
điều này làm kỹ thuật 2 (giới hạn tần suất `detect()` ở mục 38, `MIN_DETECT_INTERVAL_MS≈66ms`) LẦN
ĐẦU TIÊN thực sự có tác dụng (trước đây client tự chặn ở 80ms nên ngưỡng 66ms không bao giờ chạm
tới - kỹ thuật 2 coi như "ngủ đông" cho tới bản sửa này).

Cập nhật `templates/products/detail.html`: `tryon.js?v=3` → `?v=4` (bump cache-busting cho thay đổi
`CAPTURE_INTERVAL_MS`).

### Chưa làm / giới hạn

- KHÔNG có webcam thật để tự cảm nhận FPS mới có mượt hơn rõ rệt không - người dùng cần tự mở lại
  trang, thử lại, xem log `[TryOn][GiaiDoan3] FPS~=...` trong console server để so sánh với trước.
- Nếu máy người dùng yếu hơn máy dev (CPU chậm hơn, webcam độ phân giải cao hơn 640×480), 40ms có
  thể hơi tham vọng - `waitingForResponse` sẽ tự bảo vệ khỏi "đổ vỡ" (không bao giờ dồn ứ hàng đợi),
  nhưng nếu vẫn thấy giật, thử tăng `CAPTURE_INTERVAL_MS` lên 50-60 rồi bump lại số `?v=` template.

### Cập nhật - người dùng add lại ảnh Dublin.png (cùng phiên)

Người dùng ghi đè `media/tryon/glasses/Dublin.png` bằng 1 bản khác (kích thước file đổi
935.685 → 997.594 bytes, nhưng nội dung/kích thước ảnh và phân bố độ sáng gần như giống hệt bản
cũ) - vẫn CHƯA có kênh alpha (như lần đầu). Đã xử lý lại ĐÚNG quy trình cũ: tách nền bằng cùng
ngưỡng (225-245), ghi đè `Dublin_f.png`, xác nhận `_find_lens_anchors` vẫn tự tìm đúng 2 tâm tròng
kính (toạ độ gần như không đổi: lệch <1px so với lần trước), render thử lên ảnh mặt test cho kết
quả giống hệt. KHÔNG cần sửa migration/DB - `GlassesOverlay` (pk=3) đã trỏ sẵn tới đúng tên file
`tryon/glasses/Dublin_f.png`, ghi đè nội dung file là tự động nhận, không cần chạy lại `migrate`.

Ghi chú ngoài lề (không phải việc của phiên này): phát hiện `git status` có sẵn 1 số thay đổi ĐÃ
STAGE mà KHÔNG do Claude Code chạy `git add` (`img.png`/`img_1.png`/`img_2.png` bị đánh dấu xoá,
`media/tryon/glasses/Dublin.png` bản CŨ bị đánh dấu thêm mới) - đã báo cho người dùng, không tự ý
xử lý (không unstage, không commit) vì không rõ nguồn gốc; nhiều khả năng do 1 công cụ Git khác
(VD: GitHub Desktop, extension Git của VS Code...) người dùng đang chạy song song thao tác.

---

## 42. DỌN TRANG QUẢN TRỊ (admin) + THÊM ĐƠN VỊ VẬN CHUYỂN/TRẠNG THÁI GIAO HÀNG

Yêu cầu: dọn trang `/admin` (bỏ Giỏ hàng/Danh sách yêu thích, đưa Đơn hàng lên đầu, bỏ các đoạn
"note" kiểu ghi chú đồ án/giả lập khỏi form Đơn hàng và những chỗ tương tự), thêm chọn đơn vị vận
chuyển lúc đặt hàng + trạng thái giao hàng admin sửa được, sửa email/SĐT "khách hàng ảo" dùng để
seed đánh giá, và dọn form sửa User (bỏ khối băm mật khẩu + bỏ trường "Nhóm").

### Dọn trang admin

- `cart/admin.py`, `favorites/admin.py`: bỏ `@admin.register(...)` của `Cart`/`Favorite` - 2 model
  này vẫn hoạt động bình thường trên site, chỉ không còn hiện trong `/admin` nữa.
- `core/urls.py`: Django mặc định xếp các mục trên trang chủ `/admin` theo THỨ TỰ BẢNG CHỮ CÁI tên
  app, không có config nào để đổi thứ tự sẵn có → monkeypatch `admin.site.get_app_list` (gọi lại
  bản gốc của `AdminSite` rồi `sort()` theo khoá `app_label != "orders"`, ổn định nên phần còn lại
  vẫn giữ nguyên thứ tự cũ) để đưa app "orders" lên đầu danh sách + thanh điều hướng bên trái.
- `orders/models.py`: xoá 3 `help_text` kiểu "Đồ án không mô phỏng...", "Đồ án GIẢ LẬP bước thanh
  toán...", "Bắt buộc nhập trước khi thanh toán..." (hiện ngay dưới field tương ứng ở trang chi
  tiết Đơn hàng /admin) - đây là 3 chỗ DUY NHẤT trong toàn bộ `help_text`/nội dung hiển thị công
  khai có giọng văn "ghi chú đồ án/giả lập" sau khi rà lại TOÀN BỘ `help_text` của mọi app
  (accounts/cart/products/favorites/reviews/tryon/wallet) bằng `grep` - các app khác đều là mô tả
  field bình thường, không đụng tới. Cũng bỏ đoạn `{% comment %}` tương tự trong `templates/cart/
  cart.html` (dù comment Django không hiện ra HTML, dọn cho gọn nguồn).
- `accounts/admin.py` (`CustomUserAdmin`): viết lại `fieldsets` KHÔNG kế thừa từ `UserAdmin.fieldsets`
  gốc nữa - bỏ hẳn field `"password"` (Django mặc định vẽ ở đây bảng "algorithm/iterations/salt/
  hash" + ghi chú "Mật khẩu không được lưu trữ..." - thông tin kỹ thuật không cần cho người quản
  trị), bỏ field `"groups"` (đồng bộ với `admin.site.unregister(Group)` đã có sẵn - đồ án chỉ phân
  quyền qua is_staff/is_superuser). Giữ lại `"user_permissions"` (không được yêu cầu bỏ).
  Thêm `templates/admin/accounts/user/change_list.html` (theo đúng khuôn mẫu override đã có ở
  `templates/admin/reviews/review/change_list.html`) override `content_title` rỗng để bỏ tiêu đề
  "Chọn Người dùng để thay đổi" trên trang danh sách User (tiêu đề tab trình duyệt `<title>` vẫn
  giữ nguyên, chỉ bỏ dòng H1 hiển thị trên trang).

### Đơn vị vận chuyển + trạng thái giao hàng (`orders/models.py`, `orders/admin.py`, `orders/views.py`)

- Thêm `Order.ShippingCarrier` (GHN/GHTK/SPX/Viettel Post/J&T) - người mua chọn lúc đặt hàng
  (modal thanh toán ở `templates/cart/cart.html`, validate ở `orders/views.py::checkout` giống hệt
  cách `payment_method` đang validate).
  Trường `status` (Đã giao/Đã hủy) GIỮ NGUYÊN vai trò cũ (bằng chứng đã mua cho app reviews).
- `orders/admin.py`: bỏ hẳn `has_change_permission` (trả `False` cứng trước đây) - dùng
  `readonly_fields` liệt kê MỌI field trừ `delivery_status` để chỉ mở đúng 1 field này cho admin
  sửa (đơn vẫn KHÔNG thể sửa các field lịch sử khác qua đường vòng, `has_add_permission` vẫn `False`
  như cũ). Thêm cột + bộ lọc `delivery_status`/`shipping_carrier` vào `list_display`/`list_filter`.
- `templates/orders/my_orders.html` + `static/css/style.css`: thêm badge "Vận chuyển: ..." và badge
  màu theo trạng thái giao hàng (xanh lá = thành công, xanh dương = đang vận chuyển, xám = chờ
  giao, đỏ = thất bại) cho khách xem trực tiếp trên trang "Đơn hàng của tôi".
- Migration `orders/migrations/0006_...`: `makemigrations orders` + `migrate orders`, sau đó
  `makemigrations --check --dry-run` sạch.

### Sửa dữ liệu "khách hàng ảo" (`reviews/management/commands/seed_reviews.py`)

- Đổi `SEED_EMAIL_SUFFIX` từ `@seed.chuyendetn.local` (lộ liễu, trông rõ là dữ liệu giả) sang
  `@gmail.com`. Vì hậu tố mới không còn phân biệt được với email thật, đổi luôn cách nhận diện để
  `--reset` xoá đúng user ảo: từ `email__iendswith=...` sang `username__in=SEED_USERNAMES` (an toàn
  hơn, không phụ thuộc email).
  Thêm `SEED_PHONE_NUMBERS` (15 số hợp lệ, khớp thứ tự `SEED_USERNAMES`) vì trước đây `phone_number`
  luôn để trống.
- **Không chạy `--reset`** để tránh xoá theo cascade toàn bộ đơn hàng/đánh giá đã seed trước đó
  (đúng cảnh báo trong bộ nhớ về sự cố cũ) - thay vào đó sửa vòng lặp `handle()` để mỗi lần chạy
  lệnh (kể cả không `--reset`) đều ĐỒNG BỘ LẠI email/SĐT cho user đã tồn tại nếu khác dữ liệu seed
  hiện tại, rồi chạy `python manage.py seed_reviews` (không cờ) một lần để áp dụng ngay cho 15 user
  đã có sẵn trong DB - xác minh lại bằng truy vấn DB thật: cả 15 user đều còn nguyên đơn hàng/đánh
  giá cũ, chỉ email (→ `*.gmail.com`) và SĐT (trước đó rỗng) được cập nhật.

### Tự kiểm tra bằng luồng thật (Django `test.Client` + truy vấn DB trực tiếp, không chỉ đọc code)

- `/admin/cart/cart/` và `/admin/favorites/favorite/` → **404** (đã gỡ khỏi admin).
- Trang chủ `/admin/`: app "orders" xuất hiện ĐẦU TIÊN trong HTML (trước products/tryon/accounts/
  wallet/reviews) - xác nhận bằng vị trí ký tự xuất hiện đầu tiên của mỗi link app trong response.
- `/admin/accounts/user/<id>/change/`: không còn chữ "algorithm"/"pbkdf2"/"Mật khẩu không được lưu
  trữ" trong HTML trả về; không còn field `name="groups"`; vẫn còn `name="user_permissions"`.
- `/admin/accounts/user/`: không còn `<h1>Chọn Người dùng để thay đổi</h1>` trong HTML (title tab
  trình duyệt vẫn còn, đúng ý định).
- `/admin/orders/order/<id>/change/`: field `delivery_status` là `<select>` sửa được, các field
  còn lại (kể cả `status`) không render input sửa được. **POST thật** đổi `delivery_status` sang
  `IN_TRANSIT` (kèm đủ management-form của inline `OrderItem`) → HTTP 302 (lưu thành công), DB xác
  nhận đổi đúng giá trị - sau đó set lại `DELIVERED` để không để sai lệch dữ liệu đơn thật (#79).
- Luồng đặt hàng đầu-cuối thật (user tạm thời, xoá sạch sau khi xong + hoàn lại đúng tồn kho):
  thêm sản phẩm vào giỏ → POST `/don-hang/dat-hang/` với `shipping_carrier=SPX` → **302** →
  `Order` tạo đúng `shipping_carrier=SPX`, `delivery_status=DELIVERED` mặc định; trang "Đơn hàng
  của tôi" hiện đúng badge "Vận chuyển: SPX Express" + "Giao hàng thành công"; trang giỏ hàng hiện
  đúng 5 lựa chọn đơn vị vận chuyển.
- `manage.py check` sạch, `makemigrations --check --dry-run` sạch.

### Chưa làm / để ngỏ

- ~~Chưa dọn các tài khoản test còn sót lại~~ → đã xoá trong phiên tiếp theo, xem mục "Dọn tài
  khoản test cũ" ngay dưới đây.

### Dọn tài khoản test cũ (cùng phiên tiếp theo)

Người dùng xác nhận xoá 13 tài khoản test còn sót từ các phiên trước (`testuser*`, `testmerge*`,
`testorder*`, `pwtest*`, `pwdebug*`, `pwprofile*`, toàn bộ email `@example.com`, không phải
superuser/staff). Trước khi xoá đã kiểm tra từng tài khoản có `Order` hay không (sợ cascade xoá đơn
làm "rò rỉ" tồn kho nếu đơn còn ở trạng thái chưa hủy) - cả 4 đơn liên quan (testorder*/pwtest*)
đều đã ở trạng thái `CANCELLED` từ trước (tồn kho đã được hoàn lại đúng lúc hủy), nên xoá an toàn,
không cần chỉnh tồn kho. Không tài khoản nào có Review.

Xoá bằng `User.objects.filter(pk__in=...).delete()` → cascade đúng 62 dòng (13 User, 13 Cart, 13
Favorite, 13 Wallet, 4 Order, 4 OrderItem). Xác minh lại danh sách User còn lại: chỉ còn `admin`,
tài khoản thật của người dùng (`Minh`/`Minh_1008`/`minh123`) và đúng 15 "khách hàng ảo" seed đánh
giá (mục 42) - không đụng tới `minh123` dù không nằm trong yêu cầu ban đầu, vì không khớp mẫu tên
test và dùng chung email thật với tài khoản `Minh`.

---

## 43. XOÁ TOÀN BỘ `help_text` KHỎI ADMIN + SỬA DANH MỤC "Square" + DỌN DỮ LIỆU VÍ ẢO

Yêu cầu: người dùng cho rằng `help_text` (note hiển thị dưới mỗi field trong `/admin`) ở TẤT CẢ
model đều dư thừa, không chỉ 3 chỗ giọng "đồ án/giả lập" đã xoá ở mục 42 - xoá hết. Đổi tên danh
mục "Vuông (Square)" thành "Square". Hỏi lịch sử giao dịch ví điện tử có phải dữ liệu Claude tự
tạo hay không, nếu không cần thì xoá.

### Xoá `help_text`

Rà lại bằng `grep` toàn bộ `models.py` của 8 app (accounts/cart/products/favorites/orders/reviews/
tryon/wallet) - xoá SẠCH 29 `help_text` (giữ nguyên `verbose_name`, không đụng field nào khác).
`makemigrations` (không chỉ định app, để bắt hết 8 app cùng lúc) → 7 migration mới (accounts,
cart, favorites, orders 0007, products, reviews, tryon, wallet) → `migrate` chạy sạch.
Xác minh bằng `test.Client` thật: trang sửa Sản phẩm trong `/admin` không còn `<div class="help">`
nào, không còn bất kỳ đoạn text note nào của 4 field mẫu người dùng nêu.

### Đổi tên danh mục "Vuông (Square)" → "Square"

Chỉ có đúng 2 danh mục trong CSDL (`Oval`, `Vuông (Square)`) - đổi `name`/`slug` của danh mục pk=10
thành `"Square"`/`"square"` (khớp quy ước tên tiếng Anh thuần của danh mục còn lại `"Oval"`/`"oval"`).
Phát hiện thêm: `seed_products.sql` (script seed dữ liệu ban đầu, idempotent qua `WHERE NOT EXISTS`)
vẫn tham chiếu slug cũ `vuong-square` ở 4 chỗ - nếu không sửa, lỡ chạy lại file này sau này sẽ tạo
ra 1 danh mục "Vuông (Square)" DUPLICATE (vì điều kiện `NOT EXISTS` kiểm tra đúng slug cũ, giờ
không còn tồn tại nữa) → đã sửa cả 4 chỗ trong `seed_products.sql` sang `Square`/`square` để file
này vẫn idempotent đúng nếu chạy lại. Xác minh qua `test.Client`: trang chủ hiện đúng "Square",
không còn "Vuông (Square)" ở đâu.

### Lịch sử giao dịch ví điện tử - XÁC NHẬN là dữ liệu test, đã xoá

Điều tra trước khi trả lời (không đoán): `wallet/urls.py` KHÔNG TỒN TẠI, dòng include trong
`core/urls.py` đang bị comment (`# path('wallet/', include('wallet.urls'))`) - tính năng Ví điện
tử CHƯA từng được nối vào site thật, không trang nào (kể cả template) hiển thị số dư/lịch sử giao
dịch cho người dùng. `orders/views.py::checkout` hiện tại KHÔNG hề gọi `Wallet.withdraw()`. Kiểm
tra 9 dòng `Transaction` hiện có trong CSDL: toàn bộ mô tả đều là log test thủ công từ các phiên
trước ("Nap them test checkout admin", "Nap test checkout admin", "Nạp tiền test checkout", "Nap
them de test upload anh") - đúng là dữ liệu Claude tự tạo lúc test tính năng, KHÔNG phải dữ liệu
mô phỏng có chủ đích (khác với 15 "khách hàng ảo" ở mục 42, vốn được thiết kế có chủ đích để demo
tính năng đánh giá). Đã xoá toàn bộ 9 `Transaction` + reset `balance` về 0 cho 2 ví có số dư khác 0
(giữ nguyên record `Wallet` vì được signal tự tạo 1-1 với User, xoá hẳn có thể gây lỗi ở chỗ khác
truy cập `user.wallet`). Đã báo lại cho người dùng: tính năng Ví hiện đang "nằm im" (model + admin
có sẵn nhưng chưa có URL/giao diện nạp tiền thật), không tự ý làm thêm gì ngoài xoá dữ liệu test.

### Tự kiểm tra bằng luồng thật

`manage.py check` sạch, `makemigrations --check --dry-run` sạch. `test.Client` xác nhận: form sửa
Sản phẩm/admin không còn help text nào; trang chủ hiện đúng tên danh mục mới; `Transaction`
changelist load bình thường (200, rỗng).

---

## 44. THÊM CHỨC NĂNG "QUÊN MẬT KHẨU"

Người dùng báo thiếu chức năng quên mật khẩu. Do dự án CHƯA cấu hình gửi email thật (không có
SMTP trong `.env`), hỏi người dùng chọn giữa 3 cách (xác minh qua SĐT/email đã đăng ký - không cần
email thật; email qua console chỉ demo local; email thật qua SMTP cần cung cấp tài khoản Gmail) -
người dùng chọn **cách 1**.

### Thiết kế luồng 2 bước (`accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`)

- Bước 1 (`/tai-khoan/quen-mat-khau/`, `ForgotPasswordVerifyForm`): nhập username + email HOẶC SĐT
  đã đăng ký, đối chiếu với hồ sơ User đã lưu. Luôn trả về CÙNG MỘT thông báo lỗi chung dù username
  không tồn tại hay email/SĐT không khớp - không lộ ra tài khoản nào có tồn tại (chống dò tài khoản).
- Khớp → lưu `user.pk` + timestamp vào session (khoá `password_reset_verified_user_id`/`_at`, hết
  hạn sau 10 phút) → chuyển sang bước 2.
- Bước 2 (`/tai-khoan/dat-lai-mat-khau/`, `SetNewPasswordForm`): đặt mật khẩu mới, chạy đúng
  `AUTH_PASSWORD_VALIDATORS` đã khai báo trong `settings.py` (giống lúc đăng ký, không cho mật
  khẩu quá yếu), 2 lần nhập phải khớp nhau. Nếu vào thẳng URL này mà chưa qua bước 1 hoặc phiên xác
  minh đã hết hạn → bật lại về bước 1 kèm thông báo. Đặt lại thành công → xoá session xác minh,
  chuyển về trang đăng nhập.
- Ghi rõ trong docstring `ForgotPasswordVerifyForm`: cách xác minh này yếu hơn gửi link qua email
  thật (biết được username + email/SĐT của người khác cũng reset hộ được) - đánh đổi đã được người
  dùng đồng ý chọn cho quy mô đồ án, không phải sơ suất.
- Thêm link "Quên mật khẩu?" ở `templates/accounts/login.html`, 2 template mới
  (`forgot_password.html`, `reset_password.html`) theo đúng khuôn mẫu `.auth-card` có sẵn.

### Tự kiểm tra bằng luồng thật (user tạm thời, xoá sau khi xong)

Qua `test.Client`: sai username → lỗi chung; đúng username sai email/SĐT → lỗi chung; đúng username
+ đúng email HOẶC đúng SĐT → sang được bước 2; 2 mật khẩu nhập lại không khớp → báo lỗi; mật khẩu
yếu (`12345678`) → bị `AUTH_PASSWORD_VALIDATORS` chặn; đặt lại thành công → mật khẩu CŨ hết tác
dụng (`authenticate()` trả `None`), mật khẩu MỚI đăng nhập được; vào lại `/dat-lai-mat-khau/` sau
khi đã dùng xong → bị đá về bước 1 kèm thông báo "hết hạn" (session đã bị xoá đúng). `manage.py
check` sạch (không đổi model nên không cần migration).

---

## 45. FIX LỖI "GIỎ HÀNG/ĐƠN HÀNG KHÔNG HIỆN ĐƠN CŨ, ĐẶT ĐƠN MỚI XONG MỚI HIỆN"

### Điều tra trước khi sửa (không đoán mù)

Người dùng báo: vào trang không thấy các đơn cũ đã đặt, đặt đơn MỚI xong thì mới thấy lại (kể cả
đơn cũ). Kiểm tra `orders/views.py::my_orders` (query `Order.objects.filter(user=...).order_by(
"-created_at")`, không slice/không filter ngày) - **đúng 100%**, xác nhận bằng cách render qua
`test.Client` cho user `minh123` (có sẵn 3 đơn thật #79/#81/#82 tạo trong 2 ngày gần đây): trang
trả về đúng cả 3 đơn, đúng thứ tự, khớp DB tuyệt đối. `grep` toàn bộ project: KHÔNG có `cache_page`/
`never_cache`/`Cache-Control` ở bất kỳ đâu - tức là không trang nào chủ động chặn cache trình
duyệt.

**Kết luận nguyên nhân**: không phải lỗi query/logic phía server, mà là **cache phía trình duyệt**
(cơ chế "back-forward cache" khi bấm nút Back, hoặc cache HTTP thông thường) - trang "Đơn hàng của
tôi"/"Giỏ hàng" bị trình duyệt lưu lại "ảnh chụp" từ lần tải trước (lúc chưa có đủ đơn), hiển thị
lại y hệt bản cũ thay vì tải mới. Chỉ có luồng đặt hàng (POST → redirect → GET) mới chắc chắn né
được cache này vì đó luôn là một điều hướng MỚI, nên sau khi đặt đơn mới, trang mới hiện đúng lại.

### Sửa

Thêm `@never_cache` (Django, set `Cache-Control: no-store` buộc trình duyệt luôn tải lại, không
dùng snapshot cache/back-forward cache) cho `orders/views.py::my_orders` (trang được báo lỗi) và
`cart/views.py::cart_view` (người dùng gọi chung khu vực này là "giỏ hàng", cùng dạng trang hiển
thị dữ liệu riêng-theo-user nên cùng nguy cơ bị cache y hệt).

### Tự kiểm tra

`manage.py check` sạch. `test.Client` xác nhận cả 2 response đều có header
`Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private` sau khi thêm decorator
(trước đó không có header này).


