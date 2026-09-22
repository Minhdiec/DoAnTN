# Sơ đồ ERD dạng bảng - Dự án Astraea

Tài liệu này mô tả toàn bộ cơ sở dữ liệu của hệ thống Astraea dưới dạng bảng (thay cho hình vẽ), được phân tích trực tiếp từ mã nguồn các model Django (`accounts`, `products`, `cart`, `favorites`, `orders`, `reviews`, `tryon`, `wallet`) tại thời điểm viết tài liệu. Nội dung khớp 1-1 với sơ đồ hình vẽ `Astraea_ERD.drawio` và file `Astraea_DataDictionary.docx` đi kèm.

**Tổng quan:** 15 bảng dữ liệu, 19 quan hệ.

## Mục lục các bảng

1. [User](#1-user) — `accounts_user`
2. [Category](#2-category) — `products_category`
3. [Product](#3-product) — `products_product`
4. [ProductImage](#4-productimage) — `products_productimage`
5. [Cart](#5-cart) — `cart_cart`
6. [CartItem](#6-cartitem) — `cart_cartitem`
7. [Favorite](#7-favorite) — `favorites_favorite`
8. [Favorite_Product](#8-favoriteproduct) — `favorites_favorite_products`
9. [Order](#9-order) — `orders_order`
10. [OrderItem](#10-orderitem) — `orders_orderitem`
11. [Review](#11-review) — `reviews_review`
12. [ReviewMedia](#12-reviewmedia) — `reviews_reviewmedia`
13. [GlassesOverlay](#13-glassesoverlay) — `tryon_glassesoverlay`
14. [Wallet](#14-wallet) — `wallet_wallet`
15. [Transaction](#15-transaction) — `wallet_transaction`

## 1. Danh sách bảng và cấu trúc trường dữ liệu

### 1. User

**Tên bảng vật lý:** `accounts_user`

Tài khoản người dùng (kế thừa AbstractUser của Django, bổ sung các trường riêng cho website thương mại điện tử).

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh người dùng |
| username |  | VARCHAR(150) | Tên đăng nhập (kế thừa AbstractUser) |
| email |  | VARCHAR(254) | Email (kế thừa AbstractUser) |
| password |  | VARCHAR(128) | Mật khẩu đã mã hóa (kế thừa AbstractUser) |
| phone_number |  | VARCHAR(15) | Số điện thoại |
| address |  | VARCHAR(255) | Địa chỉ |
| avatar |  | IMAGE | Ảnh đại diện |
| created_at |  | DATETIME | Ngày tạo tài khoản |

### 2. Category

**Tên bảng vật lý:** `products_category`

Danh mục sản phẩm.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh danh mục |
| name |  | VARCHAR(100), UNIQUE | Tên danh mục |
| slug |  | VARCHAR(120), UNIQUE | Đường dẫn thân thiện |
| created_at |  | DATETIME | Ngày tạo |

### 3. Product

**Tên bảng vật lý:** `products_product`

Một sản phẩm cụ thể được bày bán trên website.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh sản phẩm |
| category_id | FK -> Category | INT | Danh mục của sản phẩm |
| created_by_id | FK -> User | INT, NULL | Người tạo/quản trị sản phẩm |
| name |  | VARCHAR(200) | Tên sản phẩm |
| slug |  | VARCHAR(220), UNIQUE | Đường dẫn thân thiện |
| description |  | TEXT | Mô tả sản phẩm |
| price |  | DECIMAL(12,2) | Giá bán (VNĐ) |
| stock_quantity |  | INT UNSIGNED | Số lượng tồn kho |
| gender |  | VARCHAR(10) {nu, nam, unisex} | Giới tính phù hợp |
| image |  | IMAGE | Ảnh chính của sản phẩm |
| is_active |  | BOOLEAN | Đang bày bán hay không |
| sku |  | VARCHAR(64) | Mã sản phẩm (SKU) |
| specs |  | JSON | Thông số kỹ thuật |
| care_instructions |  | TEXT | Hướng dẫn bảo quản |
| created_at |  | DATETIME | Ngày tạo |
| updated_at |  | DATETIME | Ngày cập nhật gần nhất |

### 4. ProductImage

**Tên bảng vật lý:** `products_productimage`

Ảnh phụ (gallery) của một sản phẩm.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh ảnh |
| product_id | FK -> Product | INT | Sản phẩm sở hữu ảnh |
| image |  | IMAGE | Tệp ảnh |
| position |  | INT UNSIGNED | Thứ tự hiển thị |

### 5. Cart

**Tên bảng vật lý:** `cart_cart`

Giỏ hàng của một người dùng, hoặc của khách vãng lai (theo session).

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh giỏ hàng |
| user_id | FK -> User | INT, NULL, UNIQUE | Chủ giỏ hàng (rỗng nếu là khách vãng lai) |
| session_key |  | VARCHAR(40), NULL, UNIQUE | Khóa phiên (giỏ hàng khách vãng lai) |
| created_at |  | DATETIME | Ngày tạo |

### 6. CartItem

**Tên bảng vật lý:** `cart_cartitem`

Một dòng sản phẩm trong giỏ hàng.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh dòng giỏ hàng |
| cart_id | FK -> Cart | INT | Giỏ hàng chứa dòng này |
| product_id | FK -> Product | INT | Sản phẩm |
| quantity |  | INT UNSIGNED (>=1) | Số lượng |
| added_at |  | DATETIME | Thời gian thêm vào giỏ |

### 7. Favorite

**Tên bảng vật lý:** `favorites_favorite`

Danh sách yêu thích của một người dùng.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh danh sách yêu thích |
| user_id | FK -> User | INT, UNIQUE | Chủ danh sách |
| created_at |  | DATETIME | Ngày tạo |

### 8. Favorite_Product

**Tên bảng vật lý:** `favorites_favorite_products`

Bảng trung gian Nhiều-Nhiều giữa Favorite và Product (Django tự sinh cho ManyToManyField).

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh bản ghi |
| favorite_id | FK -> Favorite | INT | Danh sách yêu thích |
| product_id | FK -> Product | INT | Sản phẩm được yêu thích |

### 9. Order

**Tên bảng vật lý:** `orders_order`

Đơn hàng - bằng chứng đã mua của toàn hệ thống.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh đơn hàng |
| user_id | FK -> User | INT | Người mua |
| status |  | VARCHAR(20) {DELIVERED, CANCELLED} | Trạng thái tổng của đơn |
| delivery_status |  | VARCHAR(20) {PENDING, IN_TRANSIT, DELIVERED, FAILED} | Trạng thái giao hàng |
| total_amount |  | DECIMAL(14,2) | Tổng tiền đơn hàng (VNĐ) |
| payment_method |  | VARCHAR(10) {COD, MOMO, CARD} | Hình thức thanh toán |
| shipping_carrier |  | VARCHAR(20) {GHN, GHTK, SPX, VIETTEL_POST, JT} | Đơn vị vận chuyển |
| recipient_name |  | VARCHAR(100) | Tên người nhận |
| shipping_address |  | VARCHAR(255) | Địa chỉ nhận hàng |
| recipient_phone |  | VARCHAR(15) | SĐT người nhận |
| created_at |  | DATETIME | Ngày đặt hàng |

### 10. OrderItem

**Tên bảng vật lý:** `orders_orderitem`

Một dòng sản phẩm trong đơn hàng (lưu lại giá tại thời điểm mua).

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh dòng đơn hàng |
| order_id | FK -> Order | INT | Đơn hàng chứa dòng này |
| product_id | FK -> Product | INT | Sản phẩm |
| quantity |  | INT UNSIGNED (>=1) | Số lượng |
| unit_price |  | DECIMAL(12,2) | Đơn giá lúc mua (VNĐ) |

### 11. Review

**Tên bảng vật lý:** `reviews_review`

Đánh giá của một User cho một Product, gắn với một OrderItem làm bằng chứng đã mua.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh đánh giá |
| product_id | FK -> Product | INT | Sản phẩm được đánh giá |
| user_id | FK -> User | INT | Người đánh giá |
| order_item_id | FK -> OrderItem | INT | Bằng chứng đã mua |
| rating |  | SMALLINT (1-5) | Số sao |
| content |  | TEXT | Nội dung đánh giá |
| is_anonymous |  | BOOLEAN | Ẩn danh |
| sentiment |  | VARCHAR(3) {POS, NEU, NEG} | Nhãn cảm xúc (AI tự động gán) |
| sentiment_confidence |  | FLOAT, NULL | Độ tin cậy dự đoán |
| created_at |  | DATETIME | Ngày đánh giá |

### 12. ReviewMedia

**Tên bảng vật lý:** `reviews_reviewmedia`

Ảnh/video đính kèm một đánh giá.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh tệp đính kèm |
| review_id | FK -> Review | INT | Đánh giá sở hữu tệp |
| file |  | FILE | Đường dẫn tệp |
| media_type |  | VARCHAR(5) {image, video} | Loại tệp |

### 13. GlassesOverlay

**Tên bảng vật lý:** `tryon_glassesoverlay`

Ảnh AR (thử kính ảo) gắn với đúng một Product.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh bản ghi |
| product_id | FK -> Product | INT, UNIQUE | Sản phẩm kính |
| image |  | IMAGE | Ảnh PNG nền trong suốt |
| width_ratio |  | FLOAT | Tỉ lệ bề rộng (chế độ dự phòng) |
| vertical_offset |  | FLOAT | Độ lệch dọc (chế độ dự phòng) |
| created_at |  | DATETIME | Ngày tạo |
| updated_at |  | DATETIME | Ngày cập nhật gần nhất |

### 14. Wallet

**Tên bảng vật lý:** `wallet_wallet`

Ví điện tử của một người dùng.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh ví |
| user_id | FK -> User | INT, UNIQUE | Chủ ví |
| balance |  | DECIMAL(14,2) | Số dư (VNĐ) |
| created_at |  | DATETIME | Ngày tạo ví |
| updated_at |  | DATETIME | Lần cập nhật gần nhất |

### 15. Transaction

**Tên bảng vật lý:** `wallet_transaction`

Lịch sử một giao dịch (nạp tiền hoặc thanh toán) của ví điện tử.

| Tên trường | Khóa | Kiểu dữ liệu | Mô tả |
| --- | --- | --- | --- |
| **id** | PK | INT (auto) | Định danh giao dịch |
| wallet_id | FK -> Wallet | INT | Ví điện tử liên quan |
| transaction_type |  | VARCHAR(10) {DEPOSIT, PAYMENT} | Loại giao dịch |
| amount |  | DECIMAL(14,2) | Số tiền giao dịch (VNĐ) |
| balance_after |  | DECIMAL(14,2) | Số dư sau giao dịch (VNĐ) |
| description |  | VARCHAR(255) | Ghi chú |
| created_at |  | DATETIME | Thời gian giao dịch |

## 2. Bảng tổng hợp quan hệ giữa các bảng (ký hiệu "Có" - Merise)

Cặp `(min; max)` thể hiện số lần tối thiểu/tối đa một bản ghi của bảng đó tham gia vào quan hệ, đúng theo ký hiệu dùng trong ERD hình vẽ.

| Bảng nguồn | Cardinality nguồn | Quan hệ | Cardinality đích | Bảng đích | Loại quan hệ | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| User | (0;1) | Có | (0;1) | Cart | OneToOne (tùy chọn cả hai phía) | Một người dùng sở hữu tối đa một giỏ hàng; giỏ hàng khách vãng lai không gắn User. |
| Cart | (0;n) | Có | (1;1) | CartItem | One-to-Many (bắt buộc) | Giỏ hàng chứa nhiều dòng sản phẩm. |
| Product | (0;n) | Có | (1;1) | CartItem | One-to-Many (bắt buộc) | Sản phẩm xuất hiện trong nhiều dòng giỏ hàng. |
| Category | (0;n) | Có | (1;1) | Product | One-to-Many (bắt buộc) | Một danh mục có nhiều sản phẩm; sản phẩm bắt buộc có danh mục. |
| User | (0;n) | Có | (0;1) | Product | One-to-Many (tùy chọn phía Product) | Người quản trị tạo ra nhiều sản phẩm (created_by, SET_NULL khi xóa). |
| Product | (0;n) | Có | (1;1) | ProductImage | One-to-Many (bắt buộc) | Một sản phẩm có nhiều ảnh gallery. |
| User | (0;1) | Có | (1;1) | Favorite | OneToOne (bắt buộc phía Favorite) | Một người dùng có tối đa một danh sách yêu thích. |
| Favorite | (0;n) | Có | (1;1) | Favorite_Product | Many-to-Many (qua bảng trung gian) | Danh sách yêu thích chứa nhiều sản phẩm. |
| Product | (0;n) | Có | (1;1) | Favorite_Product | Many-to-Many (qua bảng trung gian) | Sản phẩm được nhiều người yêu thích. |
| User | (0;n) | Có | (1;1) | Order | One-to-Many (bắt buộc) | Người dùng đặt nhiều đơn hàng. |
| Order | (0;n) | Có | (1;1) | OrderItem | One-to-Many (bắt buộc) | Đơn hàng chứa nhiều dòng sản phẩm. |
| Product | (0;n) | Có | (1;1) | OrderItem | One-to-Many (bắt buộc) | Sản phẩm xuất hiện trong nhiều dòng đơn hàng. |
| Product | (0;n) | Có | (1;1) | Review | One-to-Many (bắt buộc) | Sản phẩm nhận nhiều đánh giá. |
| User | (0;n) | Có | (1;1) | Review | One-to-Many (bắt buộc) | Người dùng viết nhiều đánh giá (mỗi user tối đa 1 review/product theo unique_together). |
| OrderItem | (0;n) | Có | (1;1) | Review | One-to-Many (bắt buộc) | Một dòng đơn hàng là bằng chứng đã mua cho đánh giá. |
| Review | (0;n) | Có | (1;1) | ReviewMedia | One-to-Many (bắt buộc) | Một đánh giá có nhiều ảnh/video đính kèm. |
| Product | (0;1) | Có | (1;1) | GlassesOverlay | OneToOne (bắt buộc phía GlassesOverlay) | Một sản phẩm kính có tối đa một ảnh AR. |
| User | (0;1) | Có | (1;1) | Wallet | OneToOne (bắt buộc phía Wallet) | Một người dùng có tối đa một ví điện tử. |
| Wallet | (0;n) | Có | (1;1) | Transaction | One-to-Many (bắt buộc) | Một ví có nhiều giao dịch (nạp/thanh toán). |

## 3. Ghi chú phân tích

- **Khóa chính (PK):** mọi bảng dùng khóa thay thế tự tăng `id` (mặc định của Django ORM).
- **Khóa ngoại (FK):** được đặt tên theo quy ước Django `<field>_id`, trỏ tới `id` của bảng tham chiếu.
- **Quan hệ Một-Một (OneToOne):** User↔Cart, User↔Favorite, User↔Wallet, Product↔GlassesOverlay. Trong đó User↔Cart là tùy chọn ở cả hai chiều (giỏ hàng khách vãng lai không có User); ba quan hệ còn lại bắt buộc ở chiều bảng con.
- **Quan hệ Nhiều-Nhiều (ManyToMany):** chỉ có Favorite↔Product, được Django tự sinh thành bảng trung gian `favorites_favorite_products` (mô hình hóa lại thành thực thể `Favorite_Product` trong tài liệu này để thể hiện đúng dạng bảng quan hệ).
- **Trường tiền tệ:** `Product.price`, `OrderItem.unit_price`, `Order.total_amount`, `Wallet.balance`, `Transaction.amount`, `Transaction.balance_after` đều dùng `DECIMAL`, không dùng `FLOAT`, để tránh sai số làm tròn khi tính toán tài chính.
- **Trường do AI gán:** `Review.sentiment` và `Review.sentiment_confidence` được mô hình học máy tự động điền khi lưu đánh giá, không do người dùng nhập trực tiếp.
- **Ràng buộc nghiệp vụ không thể hiện ở DB:** `Review` gắn với `OrderItem` để làm bằng chứng đã mua (kiểm tra ở tầng view, không phải ràng buộc `UNIQUE` trong DB); `unique_together` đảm bảo mỗi `User` chỉ đánh giá một `Product` một lần.
