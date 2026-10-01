# Hướng dẫn vẽ lại Class Diagram — Astraea Eyewear

Định dạng theo đúng file mẫu `bug_promtp/classgram mẫu.png` ("Class Diagram
for University Management"): mỗi lớp là một khung 3 phần (tên lớp — thuộc
tính — phương thức), thuộc tính chỉ ghi `- tênThuộcTính` (không kiểu dữ
liệu), phương thức chỉ ghi `+ tênPhươngThức()` (không kiểu trả về, ngoặc để
trống). Quan hệ giữa các lớp chỉ vẽ bằng đường thẳng liền nét nối 2 khung,
KHÔNG ghi số bội số (1, 0..1, *...), KHÔNG dùng mũi tên hay hình thoi.

Nội dung (tên trường, tên phương thức, quan hệ nào nối với quan hệ nào) đã
được đối chiếu với mã nguồn thực tế (models.py, views.py, admin.py) — xem
mục 1 và 2 để biết vì sao mỗi phương thức được thêm vào.

---

## 1. Kết quả đối chiếu với mã nguồn

| Lớp | Thuộc tính | Thêm/Sửa/Xóa có code nghiệp vụ riêng? |
|---|---|---|
| User | Đúng, đủ | Thêm (đăng ký), Sửa (hồ sơ) — có. Xóa tài khoản — không (chỉ Admin mặc định) |
| Wallet | Đúng | Nạp/Thanh toán — có (model method dùng thật trong nghiệp vụ ví) |
| Transaction | Đúng | Không có Thêm/Sửa/Xóa — chỉ tạo tự động bên trong Wallet, cố ý bất biến |
| Favorite | Đúng | Thêm, Xóa — có (favorites/views.py::toggle) |
| Cart | Đúng | Thêm — có. Sửa/Xóa thực tế có ở cart/views.py nhưng chưa từng là phương thức → đã bổ sung |
| CartItem | Đúng | Sửa, Xóa — có (cart_update, cart_remove) |
| Category | Đúng | Không — chỉ Admin mặc định, không có view riêng |
| Product | Đúng | Không — `products/views.py` chỉ có home/detail/search (đọc dữ liệu) |
| ProductImage | Đúng | Không — chỉ inline trong Admin của Product |
| GlassesOverlay | Đúng | Không — Admin mặc định, `tryon/views.py` rỗng |
| Order | Đúng | Đặt hàng, Hủy đơn — có (checkout, cancel_order) — diagram cũ thiếu hoàn toàn |
| OrderItem | Đúng | Không có Sửa/Xóa — bằng chứng đã mua, cố ý bất biến |
| Review | Đúng | Tạo đánh giá — có (review_create). Sửa/Xóa — không có view riêng |
| ReviewMedia | Đúng | Không — tạo/xóa kèm theo Review, không tách riêng |

---

## 2. Quy ước trình bày (theo đúng file mẫu)

- Thuộc tính: `- tênThuộcTính` (không ghi kiểu dữ liệu).
- Phương thức: `+ tênPhươngThức()` (không ghi kiểu trả về, tên bằng tiếng Việt).
- Chỉ những lớp được liệt kê có Thêm/Sửa/Xóa ở mục 1 mới có đủ 3 phương
  thức đó; lớp nào không có thì không tự thêm.
- Mô tả ngắn đi kèm mỗi phương thức trong tài liệu này chỉ để bạn/Gemini
  hiểu ý nghĩa — KHÔNG đưa dòng mô tả đó vào trong khung khi vẽ.

---

## 3. Đặc tả 14 lớp (dùng để vẽ lại)

### User (app accounts)
**Thuộc tính:** id, username, password, email, first_name, last_name,
phone_number, address, avatar, is_active, is_staff, is_superuser,
last_login, date_joined, created_at

**Phương thức:**
- `dangKy()` — đăng ký tài khoản mới, tự tạo kèm Wallet/Favorite/Cart
- `suaHoSo()` — sửa thông tin cá nhân + ảnh đại diện
- `dangNhap()` — đăng nhập
- `dangXuat()` — đăng xuất
- `xacMinhQuenMatKhau()` — xác minh danh tính khi quên mật khẩu
- `datLaiMatKhau()` — đặt lại mật khẩu sau khi xác minh
- `datMatKhau()` — đặt mật khẩu (mã hóa)
- `kiemTraMatKhau()` — kiểm tra mật khẩu lúc đăng nhập
- `hienThi()`

### Wallet (app wallet)
**Thuộc tính:** id, balance, created_at, updated_at

**Phương thức:**
- `napTien()` — nạp tiền vào ví, tự tạo giao dịch kèm theo
- `thanhToan()` — trừ tiền trong ví, tự tạo giao dịch kèm theo

### Transaction (app wallet)
**Thuộc tính:** id, transaction_type, amount, balance_after, description, created_at

**Phương thức:**
- `hienThi()`

### Favorite (app favorites)
**Thuộc tính:** id, created_at

**Phương thức:**
- `themSanPham()` — thêm sản phẩm vào danh sách yêu thích
- `xoaSanPham()` — xóa sản phẩm khỏi danh sách yêu thích
- `daYeuThich()` — kiểm tra sản phẩm đã yêu thích chưa

### Cart (app cart)
**Thuộc tính:** id, session_key, created_at

**Phương thức:**
- `themSanPham()` — thêm sản phẩm vào giỏ, cộng dồn nếu đã có, giới hạn theo tồn kho
- `gopGioHang()` — gộp giỏ hàng khách vãng lai vào giỏ tài khoản vừa đăng nhập
- `tongSoLuong()` — tổng số lượng sản phẩm trong giỏ
- `tongTien()` — tổng tiền giỏ hàng

### CartItem (app cart)
**Thuộc tính:** id, quantity, added_at

**Phương thức:**
- `suaSoLuong()` — sửa số lượng sản phẩm trong giỏ
- `xoaKhoiGio()` — xóa dòng sản phẩm khỏi giỏ hàng
- `tinhThanhTien()` — thành tiền của dòng sản phẩm này

### Category (app products)
**Thuộc tính:** id, name, slug, created_at

**Phương thức:**
- `luu()` — tự sinh slug nếu chưa có rồi lưu
- `hienThi()`

### Product (app products)
**Thuộc tính:** id, name, slug, description, price, stock_quantity, gender,
image, is_active, sku, specs, care_instructions, created_at, updated_at

**Phương thức:**
- `luu()` — tự sinh slug nếu chưa có rồi lưu
- `conHang()` — kiểm tra còn hàng hay không
- `layDoanGioiThieu()` — lấy đoạn mô tả giới thiệu
- `layDanhSachDacDiem()` — lấy danh sách đặc điểm nổi bật

### ProductImage (app products)
**Thuộc tính:** id, image, position

**Phương thức:**
- `hienThi()`

### GlassesOverlay (app tryon)
**Thuộc tính:** id, image, width_ratio, vertical_offset, created_at, updated_at

**Phương thức:**
- `hienThi()`

### Order (app orders)
**Thuộc tính:** id, status, delivery_status, total_amount, payment_method,
shipping_carrier, recipient_name, shipping_address, recipient_phone, created_at

**Phương thức:**
- `datHang()` — đặt hàng: tạo đơn từ giỏ hàng, trừ tồn kho, xóa giỏ hàng
- `huyDon()` — hủy đơn hàng, tự động hoàn lại tồn kho
- `hienThiHinhThucThanhToan()`
- `hienThi()`

### OrderItem (app orders)
**Thuộc tính:** id, quantity, unit_price

**Phương thức:**
- `tinhThanhTien()`

### Review (app reviews)
**Thuộc tính:** id, rating, content, is_anonymous, sentiment,
sentiment_confidence, created_at

**Phương thức:**
- `taoDanhGia()` — tạo đánh giá cho sản phẩm đã mua, tự kiểm tra điều kiện và tự gán nhãn cảm xúc bằng mô hình ML
- `hienThiTenNguoiDanhGia()`

### ReviewMedia (app reviews)
**Thuộc tính:** id, file, media_type

**Phương thức:**
- `hienThi()`

---

## 4. Danh sách quan hệ (đường thẳng liền nét, không ghi bội số)

| # | Lớp A | Lớp B | Ghi chú (không vẽ, chỉ để hiểu) |
|---|---|---|---|
| 1 | User | Wallet | Tự tạo qua signal khi User được tạo |
| 2 | Wallet | Transaction | |
| 3 | User | Favorite | Tự tạo qua signal |
| 4 | Favorite | Product | Nhiều-nhiều |
| 5 | User | Cart | Giỏ hàng khách vãng lai có thể không gắn User |
| 6 | Cart | CartItem | |
| 7 | CartItem | Product | |
| 8 | User | Product | Người tạo sản phẩm (created_by) |
| 9 | Category | Product | |
| 10 | Product | ProductImage | |
| 11 | Product | GlassesOverlay | Không phải sản phẩm nào cũng có |
| 12 | User | Order | |
| 13 | Order | OrderItem | |
| 14 | OrderItem | Product | |
| 15 | OrderItem | Review | Mỗi dòng sản phẩm đã mua đánh giá được 1 lần |
| 16 | User | Review | |
| 17 | Product | Review | |
| 18 | Review | ReviewMedia | |

---

## 5. Prompt để dán vào Gemini

```
Hãy vẽ một Class Diagram cho hệ thống website bán kính mắt "Astraea
Eyewear" (Django), theo đúng phong cách của ảnh mẫu đính kèm (khung chữ
nhật 3 phần: tên lớp ở trên cùng in đậm, kẻ ngang, danh sách thuộc tính
dạng "- tênThuộcTính" mỗi dòng một thuộc tính, kẻ ngang, danh sách phương
thức dạng "+ tênPhươngThức()" mỗi dòng một phương thức — KHÔNG ghi kiểu dữ
liệu cho cả thuộc tính lẫn phương thức). Vẽ đúng 14 lớp dưới đây, tên
phương thức viết bằng tiếng Việt, giữ đúng thứ tự đã cho, không tự thêm
phương thức nào khác. Nối các lớp bằng ĐƯỜNG THẲNG LIỀN NÉT đơn giản theo
đúng danh sách quan hệ bên dưới — KHÔNG ghi số bội số, KHÔNG dùng mũi tên,
KHÔNG dùng hình thoi, chỉ là đường nối trơn giống ảnh mẫu. Bố cục theo
nhóm nghiệp vụ: (User, Wallet, Transaction) — (Favorite, Cart, CartItem) —
(Category, Product, ProductImage, GlassesOverlay) — (Order, OrderItem) —
(Review, ReviewMedia).

[Dán nguyên phần "3. Đặc tả 14 lớp" và "4. Danh sách quan hệ" (chỉ 2 cột
Lớp A / Lớp B, bỏ cột ghi chú) ở trên vào đây]
```
