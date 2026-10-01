# Danh sách lỗi cần sửa — Sơ đồ tuần tự cũ (`sodotuantu_goc.drawio.xml`)

Giữ nguyên bố cục, số cột và số bước của file cũ. **Không thêm khung alt/opt/loop
hay ghi chú mới** — chỉ sửa đúng những chỗ ghi dưới đây.

Ký hiệu cột "Mức":
- **Bắt buộc** — sai so với UML hoặc sai so với code, dễ bị hỏi khi bảo vệ.
- **Nên** — không sai, nhưng sửa thì chính xác/đẹp hơn.

---

## Cách sửa nhanh trong draw.io

| Việc cần làm | Thao tác |
|---|---|
| Đổi mũi tên nét liền → **mũi tên trả về** (nét đứt, đầu mở) | Chọn mũi tên → Ctrl+E (Edit Style) → thêm vào cuối: `dashed=1;endArrow=open;endFill=0;endSize=8;` → Apply |
| Sửa chữ trên mũi tên | Nhấp đúp vào chữ → sửa → bấm ra ngoài |
| Chọn nhiều mũi tên cùng lúc | Giữ **Shift** rồi bấm lần lượt từng mũi tên → Edit Style một lần cho tất cả |
| Đổi tên trang | Nhấp đúp vào tên trang ở thanh dưới cùng |

---

## Trang "Hình 3.3 - Đăng nhập" — sửa nhiều nhất

### Lỗi 1 (Bắt buộc): 7 mũi tên trả về đang vẽ nét liền

Các bước **2, 7, 10, 12, 14, 17, 18** là trả kết quả về → đổi sang nét đứt, đầu mở
(thao tác ở bảng trên). Các bước còn lại giữ nét liền.

### Lỗi 2 (Bắt buộc): nhãn có `()` thừa ở cuối

Người dùng nhập liệu hay hệ thống trả kết quả không phải lời gọi hàm → bỏ `()`.

### Bảng sửa từng bước

| Bước | Từ → Đến | Nhãn cũ | Loại mũi tên cũ | Sửa thành | Mức |
|---|---|---|---|---|---|
| 1 | KH → GD | 1 : Yêu cầu trang đăng nhập() | Liền | **1 : Yêu cầu trang đăng nhập** | Bắt buộc |
| 2 | GD → KH | 2 : Trả về form đăng nhập & mã CSRF() | Liền | **2 : Trả về form đăng nhập & mã CSRF** — đổi **nét đứt** | Bắt buộc |
| 3 | KH → GD | 3 : Nhập tên đăng nhập, mật khẩu() | Liền | **3 : Nhập tên đăng nhập, mật khẩu** | Bắt buộc |
| 4 | GD → DK | 4 : Gửi yêu cầu đăng nhập (POST)() | Liền | **4 : Gửi yêu cầu đăng nhập (POST)** | Bắt buộc |
| 5 | DK → DK | 5 : Kiểm tra hợp lệ dữ liệu form() | Tự gọi | **5 : Kiểm tra hợp lệ dữ liệu form** | Bắt buộc |
| 6 | DK → CSDL | 6 : Truy vấn tài khoản theo tên() | Liền | **6 : Truy vấn tài khoản theo tên đăng nhập** | Bắt buộc |
| 7 | CSDL → DK | 7 : Trả về thông tin tài khoản() | Liền | **7 : Trả về thông tin tài khoản** — đổi **nét đứt** | Bắt buộc |
| 8 | DK → DK | 8 : Xác thực mật khẩu PBKDF2 & trạng thái() | Tự gọi | **8 : Xác thực mật khẩu & trạng thái tài khoản** | Bắt buộc |
| 9 | DK → DK | 9 : Khởi tạo phiên đăng nhập (login()) | Tự gọi | **9 : Khởi tạo phiên đăng nhập** | Nên |
| 10 | DK → GD | 10 : Thiết lập Cookie phiên (sessionid)() | Liền | **10 : Thiết lập cookie phiên đăng nhập** — đổi **nét đứt** | Bắt buộc |
| 11 | DK → GH | 11 : Lấy giỏ hàng khách theo mã phiên() | Liền | **11 : Lấy giỏ hàng khách theo mã phiên** | Bắt buộc |
| 12 | GH → DK | 12 : Trả danh sách sản phẩm trong giỏ() | Liền | **12 : Trả danh sách sản phẩm trong giỏ** — đổi **nét đứt** | Bắt buộc |
| 13 | DK → CSDL | 13 : Gộp sản phẩm vào tài khoản người dùng() | Liền | **13 : Gộp sản phẩm vào giỏ hàng của tài khoản** | Bắt buộc |
| 14 | CSDL → DK | 14 : Xác nhận gộp giỏ hàng thành công() | Liền | **14 : Xác nhận gộp giỏ hàng thành công** — đổi **nét đứt** | Bắt buộc |
| 15 | DK → GH | 15 : Xóa phiên giỏ hàng khách vãng lai() | Liền | **15 : Xoá giỏ hàng khách vãng lai** (code xoá *giỏ hàng*, không xoá phiên) | Bắt buộc |
| 16 | DK → DK | 16 : Kiểm tra quyền & chọn URL chuyển hướng() | Tự gọi | **16 : Kiểm tra quyền & chọn trang chuyển tới** | Bắt buộc |
| 17 | DK → GD | 17 : Chuyển hướng trình duyệt (HTTP 302)() | Liền | **17 : Chuyển hướng trình duyệt (HTTP 302)** — đổi **nét đứt** | Bắt buộc |
| 18 | GD → KH | 18 : Hiển thị Trang chủ / Trang quản trị() | Liền | **18 : Hiển thị Trang chủ / Trang quản trị** — đổi **nét đứt** | Bắt buộc |

### Lỗi 3 (Bắt buộc): cột "GH : Giỏ hàng vãng lai" nằm lệch giữa sơ đồ

Hộp tên cột GH đang ở ngang bước 10 (thấp hơn 4 cột kia). Trong UML, hộp tên nằm
giữa sơ đồ nghĩa là **đối tượng được tạo ra tại thời điểm đó** — sai, vì giỏ
hàng khách đã có từ trước khi đăng nhập.

Cách sửa:
1. Chọn hộp **GH : Giỏ hàng vãng lai** → tab **Arrange** → đặt **Top** bằng đúng Top
   của hộp **KH / GD / DK / CSDL** (cùng một hàng).
2. Chọn đường nét đứt bên dưới GH → kéo đầu trên của nó lên sát đáy hộp GH,
   đầu dưới bằng với đầu dưới của các cột khác.

### Lỗi 4 (Nên): kiểu vẽ khác 4 trang còn lại

Trang này dùng hộp nền vàng viền đỏ, tên dạng `KH : Khách hàng`; 4 trang sau dùng
hộp trắng viền đen, tên kèm `«Actor»`, `«Boundary»`… Nên đổi cho đồng bộ:
- Chọn 5 hộp tên cột → bảng Style bên phải: **Fill = trắng**, **Line = đen**.
- Đổi tên: `KH : Khách hàng` → `Khách hàng «Actor»`, `GD : Giao diện` →
  `Giao diện đăng nhập «Boundary»`, `DK : Bộ điều khiển` → `Bộ điều khiển đăng nhập «Control»`,
  `CSDL : Cơ sở dữ liệu` → `Cơ sở dữ liệu «Entity / MySQL»`,
  `GH : Giỏ hàng vãng lai` → `Giỏ hàng vãng lai «Entity»`.

---

## Trang "Hình 3.6 - Thêm vào giỏ hàng" — sửa nhỏ

| Bước cũ | Từ → Đến | Nhãn cũ | Sửa thành | Mức |
|---|---|---|---|---|
| 5 (nhánh Còn hàng) | DK → CSDL | 5. Lấy giỏ hàng (theo tài khoản hoặc session) | **6. Lấy giỏ hàng (theo tài khoản hoặc phiên khách)** | Nên |
| 6 | DK → CSDL | 6. Thêm hoặc cộng dồn số lượng CartItem | **7. Thêm hoặc cộng dồn số lượng (không vượt tồn kho)** | Nên |
| 7 | DK → GD | 7. Chuyển tới giỏ hàng, báo thành công | **8. Chuyển tới giỏ hàng, báo thành công** | Nên |
| 8 | GD → KH | 8. Hiển thị kết quả | **9. Hiển thị kết quả** | Nên |

Lý do đánh số lại: số **5** đang bị dùng 2 lần (nhánh Hết hàng và nhánh Còn hàng) —
đánh số liên tục cho dễ đọc, dễ trình bày.

Không có lỗi ký hiệu: mũi tên gọi/trả về đã đúng nét.

---

## Trang "Hình 3.7 - Đặt hàng & Thanh toán" — thiếu điều kiện

| Bước cũ | Từ → Đến | Nhãn cũ | Sửa thành | Mức |
|---|---|---|---|---|
| 1 | KH → GD | 1. Chọn thanh toán, vận chuyển, người nhận | **1. Chọn thanh toán (giả lập), vận chuyển, người nhận** | Nên |
| 5 | DK → DK | 5. Kiểm tra giỏ hàng, tồn kho, người nhận | **5. Kiểm tra giỏ hàng, tồn kho, thanh toán, vận chuyển, người nhận** | **Bắt buộc** (code còn kiểm tra hình thức thanh toán và đơn vị vận chuyển) |
| 6 (nhánh Hợp lệ) | DK → CSDL | 6. Tạo đơn hàng (Order) | **7. Tạo đơn hàng (Order)** | Nên |
| 7 | DK → CSDL | 7. Lưu chi tiết đơn (OrderItem), trừ tồn kho | **8. Lưu chi tiết đơn (OrderItem), trừ tồn kho** | Nên |
| 8 | DK → CSDL | 8. Xoá giỏ hàng | **9. Xoá giỏ hàng** | Nên |
| 9 | DK → GD | 9. Chuyển tới "Đơn hàng của tôi", báo thành công | **10. Chuyển tới "Đơn hàng của tôi", báo thành công** | Nên |
| 10 | GD → KH | 10. Hiển thị kết quả | **11. Hiển thị kết quả** | Nên |

Lý do đánh số lại: số **6** đang bị dùng 2 lần.

---

## Trang "Hình 3.8 - Đánh giá & Cảm xúc AI" — gần như đúng

| Bước cũ | Từ → Đến | Nhãn cũ | Sửa thành | Mức |
|---|---|---|---|---|
| 5 (nhánh Đủ điều kiện) | DK → Mô hình | 5. Gửi nội dung bình luận | **6. Gửi nội dung bình luận** | Nên |
| 6 | Mô hình → Mô hình | 6. Tách từ, TF-IDF, Logistic Regression | **7. Làm sạch, tách từ, TF-IDF, Logistic Regression** | Nên |
| 7 | Mô hình → DK | 7. Nhãn cảm xúc + độ tin cậy | **8. Nhãn cảm xúc + độ tin cậy** | Nên |
| 8 | DK → CSDL | 8. Lưu đánh giá kèm nhãn cảm xúc | **9. Lưu đánh giá kèm nhãn cảm xúc** | Nên |
| 9 | DK → CSDL | 9. Lưu tệp đính kèm (tối đa 5 file) | **10. Lưu tệp đính kèm (tối đa 5 file)** | Nên |
| 10 | DK → GD | 10. Hiển thị đánh giá kèm nhãn | **11. Hiển thị đánh giá kèm nhãn** | Nên |
| 11 | GD → KH | 11. Xem kết quả | **12. Xem kết quả** | Nên |

Chữ điều kiện `[Không đủ điều kiện]` có thể ghi rõ hơn (Nên):
**`[Chưa giao / đã đánh giá / thiếu số sao hoặc nội dung]`** — code còn chặn trường hợp
không chọn số sao hoặc bỏ trống nội dung.

---

## Trang "Hình 3.9 - Thử kính ảo AR" — sai chi tiết kỹ thuật

| Vị trí | Cũ | Sửa thành | Mức |
|---|---|---|---|
| Tên trang | Hình 3.9 - Thử kính ảo **AR** | **Hình 3.9 - Thử kính ảo** (khớp cách gọi trong báo cáo) | Nên |
| Hộp tên cột 3 | Máy chủ xử lý ảnh «Service / WebSocket» | **Máy chủ xử lý ảnh «Control / WebSocket»** (đây là nơi nhận và điều phối yêu cầu) | Nên |
| Bước 3 (nhánh Cho phép) | 3. Mở kết nối WebSocket, gửi mẫu kính | **4. Mở kết nối WebSocket, gửi mẫu kính** | Nên |
| Bước 4 | 4. Lấy ảnh kính (PNG overlay) | **5. Lấy thông tin mẫu kính (đường dẫn ảnh PNG)** | **Bắt buộc** (CSDL chỉ lưu đường dẫn, file PNG nằm trong thư mục `media/`) |
| Bước 5 | 5. Trả ảnh kính PNG | **6. Trả thông tin mẫu kính** | **Bắt buộc** |
| Bước 6 | 6. Gửi khung hình webcam (**Base64**) | **7. Gửi khung hình webcam (JPEG)** | **Bắt buộc** (`tryon.js` gửi ảnh JPEG dạng nhị phân, không phải Base64) |
| Bước 7 | 7. Nhận diện mắt, làm mượt, dán kính (MediaPipe + OpenCV) | **8. Nhận diện mắt, làm mượt, dán kính (MediaPipe + OpenCV)** | Nên |
| Bước 8 | 8. Khung hình đã ghép kính | **9. Khung hình đã ghép kính + cờ có/không có khuôn mặt** | Nên |
| Bước 9 | 9. Hiển thị hình đeo kính | **10. Hiển thị hình đeo kính** | Nên |
| Bước 10 | 10. Đóng cửa sổ | **11. Đóng cửa sổ** | Nên |
| Bước 11 | 11. Ngắt kết nối WebSocket & tắt camera | **12. Ngắt kết nối WebSocket & tắt camera** | Nên |

Lý do đánh số lại: số **3** đang bị dùng 2 lần.

---

## Đánh số hình khi chèn vào báo cáo

File cũ chỉ có 5 sơ đồ nhưng đặt tên 3.3 rồi nhảy sang 3.6 → khi chèn vào Word
đánh số lại cho liên tục:

| Tên trang trong file cũ | Số hình trong báo cáo |
|---|---|
| Hình 3.3 - Đăng nhập | **Hình 3.3.** Sơ đồ tuần tự chức năng Đăng nhập |
| Hình 3.6 - Thêm vào giỏ hàng | **Hình 3.4.** Sơ đồ tuần tự chức năng Thêm sản phẩm vào giỏ hàng |
| Hình 3.7 - Đặt hàng & Thanh toán | **Hình 3.5.** Sơ đồ tuần tự chức năng Đặt hàng và thanh toán |
| Hình 3.8 - Đánh giá & Cảm xúc AI | **Hình 3.6.** Sơ đồ tuần tự chức năng Đánh giá sản phẩm và phân loại cảm xúc |
| Hình 3.9 - Thử kính ảo AR | **Hình 3.7.** Sơ đồ tuần tự chức năng Thử kính ảo |

---

## Tổng kết số lỗi

| Trang | Bắt buộc | Nên |
|---|---|---|
| Đăng nhập | 7 mũi tên trả về sai nét + 17 nhãn thừa `()` + cột GH lệch vị trí | Đồng bộ kiểu vẽ |
| Thêm vào giỏ | — | Đánh số lại, thêm "(không vượt tồn kho)" |
| Đặt hàng | Bước 5 thiếu "thanh toán, vận chuyển" | Đánh số lại, ghi "giả lập" |
| Đánh giá | — | Đánh số lại, ghi rõ điều kiện |
| Thử kính ảo | Bước 4, 5, 6 sai chi tiết (PNG, Base64) | Đánh số lại, đổi «Control», thêm cờ, bỏ "AR" |

---
---

# RÀ SOÁT LẦN 2 — Kiểm tra luồng xử lý file `sodotuantu.xml` (bản đã sửa)

Phạm vi: chỉ kiểm tra **luồng** (thứ tự bước, ai gửi cho ai, nội dung có khớp code
không). Không xét khung alt/loop/opt. Đối chiếu với `accounts/views.py`,
`cart/services.py`, `cart/models.py`, `cart/views.py`, `orders/views.py`,
`reviews/views.py`, `tryon/consumers.py`, `static/js/tryon.js`.

## Việc 0 (Bắt buộc): xoá 5 trang cũ còn sót trong file

File `sodotuantu.xml` đang có **10 trang**. Xoá 5 trang đầu (bản cũ chưa sửa):
`Hình 3.3 - Đăng nhập` (trang **trống**), `Hình 3.6 - Thêm vào giỏ hàng`,
`Hình 3.7 - Đặt hàng & Thanh toán`, `Hình 3.8 - Đánh giá & Cảm xúc AI`,
`Hình 3.9 - Thử kính ảo AR`.

Cách xoá: chuột phải tên trang ở thanh dưới cùng → **Delete**. Còn lại đúng 5 trang
Hình 3.3 → 3.7.

## Kết quả tổng hợp

| Sơ đồ | Luồng | Cần sửa |
|---|---|---|
| 3.3 Đăng nhập | ❌ Sai thứ tự 1 bước | Xoá bước 10, gộp cookie vào bước 17 (mục A) |
| 3.4 Thêm vào giỏ | ✅ Đúng | — |
| 3.5 Đặt hàng | ✅ Đúng | (tuỳ chọn) ghi "tổng tiền" ở bước 7 (mục C) |
| 3.6 Đánh giá | ⚠️ Gần đúng | Sửa nhãn bước 5 (mục B) |
| 3.7 Thử kính ảo | ✅ Đúng | (tuỳ chọn) thêm bước đọc ảnh PNG (mục D) |

---

## A. Hình 3.3 Đăng nhập — Bắt buộc

**Lỗi:** bước 10 "Bộ điều khiển → Giao diện: Thiết lập cookie phiên đăng nhập" nằm
giữa luồng. Thực tế server **không gửi gì về trình duyệt** giữa chừng — cookie phiên
chỉ được gửi **một lần, cùng với lệnh chuyển hướng HTTP 302** ở cuối.

**Cách sửa trong draw.io:**
1. Chọn mũi tên bước 10 và thanh kích hoạt nhỏ trên cột Giao diện ngay tại đó → **Delete**.
2. Kéo các mũi tên phía dưới lên cho kín khoảng trống (hoặc để nguyên cũng được).
3. Sửa nhãn và đánh số lại theo bảng:

| Nhãn hiện tại | Sửa thành |
|---|---|
| 10 : Thiết lập cookie phiên đăng nhập | **(xoá)** |
| 11 : Lấy giỏ hàng khách theo mã phiên | 10 : Lấy giỏ hàng khách theo mã phiên |
| 12 : Trả danh sách sản phẩm trong giỏ | 11 : Trả danh sách sản phẩm trong giỏ |
| 13 : Gộp sản phẩm vào giỏ hàng của tài khoản | 12 : Gộp sản phẩm vào giỏ hàng của tài khoản |
| 14 : Xác nhận gộp giỏ hàng thành công | 13 : Xác nhận gộp giỏ hàng thành công |
| 15 : Xoá giỏ hàng khách vãng lai | 14 : Xoá giỏ hàng khách vãng lai |
| 16 : Kiểm tra quyền & chọn trang chuyển tới | 15 : Kiểm tra quyền & chọn trang chuyển tới |
| 17 : Chuyển hướng trình duyệt (HTTP 302) | **16 : Chuyển hướng trình duyệt (HTTP 302) kèm cookie phiên** |
| 18 : Hiển thị Trang chủ / Trang quản trị | **17 : Hiển thị Trang chủ / Trang quản trị, báo "Đăng nhập thành công"** |

Các bước còn lại (1–9) đúng:
- 5 → 8: Django kiểm tra form rồi mới truy vấn tài khoản, xác thực mật khẩu + trạng thái.
- 11 → 15 cũ: đúng thứ tự trong `merge_guest_cart_into_user()` → `merge_from()`
  (lấy giỏ khách → gộp từng sản phẩm → xoá giỏ khách).
- 16 cũ: đúng thứ tự trong code (có trang `next` → về `next`; là admin → trang quản trị;
  còn lại → trang chủ).

Bổ sung khi vẽ (Nên): 4 hộp tên cột đầu đang thiếu dòng khuôn mẫu — nhấp đúp và gõ
thêm «Actor», «Boundary», «Control», «Entity / MySQL».

---

## B. Hình 3.6 Đánh giá & Cảm xúc AI — Nên sửa

**Lỗi:** bước 5 "Báo lỗi không đủ điều kiện" vẽ mũi tên về *Giao diện chi tiết SP*,
nhưng code xử lý 2 kiểu:
- Đơn chưa giao / sản phẩm đã đánh giá → **chuyển về trang "Đơn hàng của tôi"** kèm lỗi.
- Thiếu số sao hoặc nội dung → quay lại trang chi tiết sản phẩm kèm lỗi.

| Nhãn hiện tại | Sửa thành |
|---|---|
| 5. Báo lỗi không đủ điều kiện | **5. Báo lỗi (chuyển về Đơn hàng của tôi / trang sản phẩm)** |

Các bước còn lại đúng: mô hình được gọi **trước khi lưu** (6 → 8), lưu đánh giá
(9) **rồi mới** lưu tệp đính kèm tối đa 5 file (10), cuối cùng quay về mục đánh giá của
trang sản phẩm (11).

---

## C. Hình 3.5 Đặt hàng & Thanh toán — Tuỳ chọn

Luồng đúng. Bước 5 kiểm tra đúng thứ tự trong code: giỏ trống → tồn kho → thanh toán →
vận chuyển → người nhận. Bước 7 → 9 đúng thứ tự trong giao dịch.

Nếu muốn đầy đủ hơn (code tính tổng tiền trước khi tạo đơn):

| Nhãn hiện tại | Có thể sửa thành |
|---|---|
| 7. Tạo đơn hàng (Order) | 7. Tạo đơn hàng (tổng tiền, thông tin nhận hàng) |

---

## D. Hình 3.7 Thử kính ảo — Tuỳ chọn

Luồng đúng: chỉ khi mở camera thành công mới kết nối WebSocket; kết nối xong mới gửi
mẫu kính; trình duyệt chỉ gửi khung mới khi đã nhận khung trước; đóng cửa sổ thì dừng
gửi, đóng WebSocket, tắt camera.

Nếu muốn đầy đủ hơn: sau bước 6, máy chủ **đọc file ảnh kính PNG và tự tìm tâm tròng
kính** trước khi bắt đầu dán. Thêm 1 mũi tên tự gọi trên cột Máy chủ:

| Vị trí | Thêm |
|---|---|
| Ngay sau "6. Trả thông tin mẫu kính" | **7. Đọc ảnh kính PNG, xác định tâm tròng kính** (tự gọi) — các bước sau đánh số lùi thêm 1 (7→8, …, 12→13) |

---

## E. Hình 3.4 Thêm vào giỏ hàng — Không cần sửa

Đúng hoàn toàn: lấy sản phẩm đang bán → kiểm tra còn hàng (hết thì báo lỗi ở trang chi
tiết) → lấy giỏ theo tài khoản hoặc phiên khách → cộng dồn số lượng (không vượt tồn
kho) → chuyển tới trang giỏ hàng, báo thành công.
