# Hướng dẫn hiểu đồ án Astraea — 2 mô-đun AI

Tài liệu này giải thích **thử kính ảo** và **phân tích cảm xúc bình luận** — hai mô-đun AI của đồ án — dựa trên việc đọc trực tiếp mã nguồn hiện có (`tryon/`, `static/js/tryon.js`, `reviews/ml/`, `phantichcamxuc/`). Chỉ liệt kê những gì thật sự có trong code, không suy đoán thêm.

---

## Phần 1: Thử kính ảo (Virtual Try-On)

### 1.1. Công nghệ dùng

| Việc | Công nghệ | Phiên bản |
|---|---|---|
| Kênh thời gian thực (server ↔ trình duyệt) | Django Channels + Daphne (ASGI, WebSocket) | channels 4.3.2, daphne 4.2.3 |
| Nhận diện landmark khuôn mặt | MediaPipe Tasks API — `FaceLandmarker`, chế độ `VIDEO` | mediapipe 0.10.35 |
| Xử lý ảnh (đọc/ghi JPEG, xoay, co giãn, chuẩn hoá sáng, ghép ảnh) | OpenCV | opencv-python 5.0.0.93 |
| Làm mượt chuyển động (chống rung/giật) | One Euro Filter (Casiez, Roussel, Vogel — 2012), tự cài đặt trong `tryon/vision.py` | — |
| Bắt hình webcam, gửi/nhận khung hình | `getUserMedia` + `WebSocket` (JavaScript thuần) | `static/js/tryon.js` |

Toàn bộ xử lý ảnh nằm ở **server** (Python). Trình duyệt chỉ lo bật camera, chụp khung hình gửi lên, và hiển thị khung hình đã xử lý nhận về.

### 1.2. Quy trình thử kính ảo, từng bước

```
Người dùng bấm nút TRY ON
        │
        ▼
getUserMedia() xin quyền camera (static/js/tryon.js::startCamera)
        │
        ▼
Mở kết nối WebSocket tới /ws/tryon/ (tryon/routing.py → TryOnConsumer)
        │
        ▼
Server: connect() tạo RIÊNG cho phiên này — 1 FaceMeshDetector
(nạp model face_landmarker.task), 1 AnchorSmoother, 1 LightNormalizer
        │
        ▼
Client gửi lệnh JSON {"action": "select_glasses", "glasses_id": ...}
→ server đọc file PNG kính, tự dò 2 tâm tròng kính, cache lại theo glasses_id
        │
        ▼
Vòng lặp mỗi 40ms (~25 khung/giây, static/js/tryon.js):
  1. Canvas chụp 1 khung từ thẻ <video>, nén JPEG chất lượng 0.8
  2. Gửi khung (binary) qua WebSocket — CHỈ gửi khung mới khi khung
     trước đã có phản hồi (biến waitingForResponse, tránh dồn ứ hàng đợi)
        │
        ▼
Server nhận khung (tryon/consumers.py::_handle_frame → _process_frame_sync):
  a. Giải mã JPEG → lật ngang (soi gương)
  b. Nếu ảnh tối (đo độ sáng có hysteresis) → chạy CLAHE chuẩn hoá sáng
  c. Chọn vùng đưa vào MediaPipe: nếu đã biết vị trí mặt từ khung trước,
     CHỈ cắt ô ROI quanh mặt rồi resize 256×256; nếu chưa biết (lần đầu/
     vừa mất mặt), thu nhỏ CẢ khung về bề rộng 400px
  d. Gọi FaceLandmarker.detect() — nhưng KHÔNG gọi mọi khung: giới hạn
     ~15 lần/giây khi đang bám vết ổn định, giữa 2 lần dùng lại toạ độ cũ
  e. Lấy toạ độ 2 khoé mắt ngoài (landmark 33 và 263)
  f. Làm mượt tâm/bề rộng/góc của 2 điểm mắt bằng One Euro Filter
  g. Dán kính lên khung hình GỐC (không phải khung đã resize) bằng phép
     biến đổi affine 2 điểm (xem mục 1.3)
  h. Mã hoá lại JPEG chất lượng 80, gửi về client: 1 byte cờ (có/không
     phát hiện mặt) + dữ liệu JPEG
        │
        ▼
Client nhận khung nhị phân → hiển thị vào thẻ <img>, xoá khung cũ khỏi
bộ nhớ (URL.revokeObjectURL) — lặp lại từ bước chụp khung tiếp theo
```

### 1.3. Xoay/co giãn kính khi quay đầu — dùng kỹ thuật gì

**Chế độ chính (tự động)**: ảnh PNG kính có 2 "tâm tròng kính" được tự động dò ra một lần khi nạp ảnh (bằng contour + ngưỡng Otsu, xem `GlassesOverlay._find_lens_anchors` trong `tryon/vision.py`). Mỗi khung hình, hệ thống tính một **phép biến đổi đồng dạng 2 điểm** (`_similarity_matrix_2pt`): ánh xạ 2 tâm tròng kính đó sang 2 điểm khoé mắt vừa nhận diện được. Phép biến đổi này gồm đúng 3 thành phần — xoay đều, co giãn đều theo một tỉ lệ, và tịnh tiến — được tính bằng số phức (`(dst2-dst1)/(src2-src1)`), nên **xoay đầu và khoảng cách 2 mắt thay đổi được xử lý CÙNG LÚC bởi một phép tính duy nhất**, không cần tách riêng "tính góc" rồi "tính tỉ lệ" như cách làm thủ công.

**Chế độ dự phòng** (khi ảnh kính không tự dò được tâm tròng kính): dùng `width_ratio` (tỉ lệ bề rộng kính so với khoảng cách 2 mắt, ví dụ 1.6) để tính hệ số co giãn = `khoảng_cách_2_mắt × width_ratio / bề_rộng_gốc_ảnh_kính`, và dùng `cv2.getRotationMatrix2D` để xoay theo góc giữa 2 điểm mắt (`math.atan2`). Người dùng chỉnh 2 số này qua thanh trượt trên giao diện, gửi lên server bằng lệnh JSON `{"action": "calibrate", ...}`.

### 1.4. Xử lý độ trễ/giật lag — các kỹ thuật cụ thể đang dùng

Toàn bộ nằm ở `tryon/consumers.py` (docstring đầu file gọi đây là "Giai đoạn 3 — tối ưu độ trễ"):

1. **Giới hạn tần suất gọi MediaPipe** (~15 lần/giây) khi đang bám vết ổn định — đây là bước tốn CPU nhất trong cả pipeline, nên không gọi lại mỗi khung.
2. **Chỉ xử lý vùng ROI quanh mặt** (256×256px, cạnh = khoảng cách 2 mắt × 2.4) thay vì quét cả khung hình, một khi đã biết mặt ở đâu từ khung trước; nếu chưa biết thì mới quét cả khung (đã thu nhỏ về 400px).
3. **One Euro Filter** làm mượt tâm/bề rộng/góc của điểm neo mắt — chống rung do nhiễu nhận diện mà không làm tăng độ trễ cảm nhận khi đầu di chuyển thật (bộ lọc tự "nới lỏng" khi tín hiệu đổi nhanh, tự "siết chặt" khi gần như đứng yên). Tham số (`min_cutoff=0.5, beta=0.015`) được đo thực nghiệm trên đúng luồng landmark bằng pixel của dự án, ghi rõ trong `tryon/vision.py`.
4. **Dung sai khi mất mặt** (`MAX_CONSECUTIVE_MISSES=3`): không xoá kính ngay khi 1 khung không nhận diện được (tránh kính "nhấp nháy" ẩn/hiện), chỉ coi là mất mặt thật sau 3 lần liên tiếp không ra kết quả.
5. **CLAHE có điều kiện** (chuẩn hoá ánh sáng): chỉ chạy khi ảnh thực sự tối (có ngưỡng hysteresis để tránh bật/tắt liên tục khi độ sáng dao động quanh biên).
6. **Cache renderer kính theo glasses_id**: ảnh PNG + vị trí tâm tròng kính chỉ đọc/dò một lần cho mỗi mẫu kính trong một phiên, đổi qua lại nhiều lần không đọc lại file.
7. Phía client (`static/js/tryon.js`): giới hạn chụp 40ms/khung (~25fps) và **backpressure** — không bao giờ gửi khung mới khi khung trước chưa có phản hồi, tránh độ trễ dồn tích luỹ khi server xử lý không kịp; webcam giới hạn 640×480, JPEG nén chất lượng 0.8 cả hai chiều gửi/nhận.

---

## Phần 2: Phân tích cảm xúc bình luận (Sentiment Analysis)

### 2.1. Hai file `.ipynb` trong dự án — file nào làm gì

Dự án có đúng 2 file notebook, mục đích khác hẳn nhau:

- **`phantichcamxuc/sentiment_analysis.ipynb`** — notebook **huấn luyện mô hình thật**, chính là nguồn cho mọi nội dung ở Phần 2 này.
- **`BUG.ipynb`** (thư mục gốc) — **không liên quan đến dữ liệu hay huấn luyện**. Đọc nội dung thì đây là nhật ký các yêu cầu sửa lỗi/chỉnh giao diện kèm ảnh chụp màn hình (ví dụ lỗi hiển thị số sao, lỗi nút giỏ hàng, yêu cầu đổi câu banner...) được dùng để giao việc sửa lỗi trong lúc phát triển — không chứa dữ liệu bình luận hay code huấn luyện mô hình nào.

### 2.2. Bộ dữ liệu và cách làm sạch

- File gốc: `phantichcamxuc/data - data.csv` — **31.460 dòng**, đã gán sẵn nhãn 3 lớp (`POS`/`NEU`/`NEG`) ở cột `label`, nội dung bình luận ở cột `comment`.
- Làm sạch (cell 5-6 của notebook):
  - Bỏ dòng thiếu nội dung/nhãn.
  - Chuẩn hoá khoảng trắng thừa, gộp dấu câu lặp (`"!!!"` → `"!"`).
  - **Giữ nguyên emoji** — vì emoji mang tín hiệu cảm xúc rõ trong bình luận mua sắm.
  - **Bỏ bình luận trùng lặp** (mẫu câu soạn sẵn của shop lặp lại nhiều lần) — nếu không bỏ, cùng một câu có thể vừa rơi vào tập train vừa vào tập test, làm kết quả đánh giá bị ảo (data leakage).
- Sau làm sạch: còn **26.706 dòng** (POS 16.148 · NEG 6.315 · NEU 4.243 — lệch lớp rõ, xử lý ở bước huấn luyện).

### 2.3. Tiền xử lý — tách từ tiếng Việt

Dùng `underthesea.word_tokenize(text, format="text")` để tách từ, ghép từ ghép bằng dấu `_` (ví dụ `"chất lượng"` → `"chất_lượng"`), giúp bước vector hoá TF-IDF hiểu đúng đơn vị từ tiếng Việt thay vì tách rời từng âm tiết. **Bước này bắt buộc giống hệt lúc dự đoán thật** — nếu khác, câu mới sẽ bị vector hoá lệch không gian đặc trưng so với lúc train.

### 2.4. Huấn luyện mô hình

- Chia tập: 80% train / 20% test, **giữ tỉ lệ nhãn** (`stratify=y`) → Train 21.364 / Test 5.342 dòng.
- Vector hoá: `TfidfVectorizer(ngram_range=(1,2), min_df=3, max_features=30000, sublinear_tf=True)` → 10.181 đặc trưng (giữ cả cụm 2 từ để phân biệt phủ định như `"không đẹp"`).
- So sánh **3 mô hình**, đều dùng `class_weight="balanced"` (vì dữ liệu lệch lớp POS): `LogisticRegression`, `ComplementNB`, `LinearSVC` (hiệu chỉnh qua `CalibratedClassifierCV` để có xác suất dự đoán).
- Chọn mô hình theo **macro-F1** (trung bình F1 của cả 3 lớp, coi trọng lớp thiểu số ngang lớp đa số) thay vì accuracy thô — vì accuracy sẽ bị lớp POS (đa số) áp đảo, che khuất việc mô hình dự đoán kém ở lớp NEU (khó nhất, ít dữ liệu nhất).

  | Mô hình | macro-F1 |
  |---|---|
  | **LogisticRegression** (được chọn) | **0.648** |
  | ComplementNB | 0.626 |
  | LinearSVC (calibrated) | 0.598 |

- Kết quả được lưu vào **`phantichcamxuc/sentiment_model.joblib`** — một dict gồm `{"vectorizer": ..., "model": ...}` (bắt buộc lưu chung, vì lúc dự đoán phải dùng đúng `vectorizer` đã fit ở bước train để ra cùng không gian đặc trưng).

### 2.5. Đưa vào website — chuyện gì xảy ra khi khách gửi đánh giá

Hàm `predict_sentiment()` ở notebook được chép gần như nguyên vẹn sang **`reviews/ml/sentiment.py`** (chỉ khác: nạp model một lần và cache lại bằng `@lru_cache`, tránh đọc lại file `.joblib` mỗi lần có đánh giá mới).

Luồng thật khi khách bấm gửi đánh giá (`reviews/views.py::review_create`):

1. Server kiểm tra điều kiện: đã đăng nhập, đơn hàng chứa sản phẩm này là của chính người dùng, đơn đã giao thành công, và chưa từng đánh giá sản phẩm này trước đó.
2. Form hợp lệ (đã chọn 1-5 sao + nhập nội dung) → tạo bản ghi `Review` với `product`, `user`, `order_item`.
3. **Ngay lúc lưu**, gọi `predict_sentiment(review.content)`:
   - Làm sạch văn bản giống hệt lúc train (`clean_text`).
   - Tách từ bằng `underthesea.word_tokenize` giống hệt lúc train.
   - `vectorizer.transform([...])` biến câu thành vector TF-IDF cùng không gian đặc trưng với lúc train.
   - `model.predict_proba(...)` ra xác suất cho cả 3 lớp; nhãn được chọn là lớp có xác suất cao nhất, độ tin cậy = chính xác suất đó.
   - Kết quả (`review.sentiment`, `review.sentiment_confidence`) được gán thẳng vào bản ghi — **người dùng không tự chọn nhãn cảm xúc, đây là bước tự động hoàn toàn**.
4. Bản ghi được lưu vào cơ sở dữ liệu (`reviews_review.sentiment`, `reviews_review.sentiment_confidence`).

Kết quả sau đó được tổng hợp và hiển thị ở 2 nơi (`products/views.py`, tính bằng một `aggregate()` đếm số lượng theo từng nhãn `Q(sentiment="POS")`/`"NEU"`/`"NEG"`):
- **Trang chi tiết sản phẩm**: tỉ lệ % Tích cực/Trung lập/Tiêu cực của đúng sản phẩm đang xem.
- **Trang quản trị** (`reviews/admin.py`): thống kê tổng toàn hệ thống và theo từng sản phẩm.
