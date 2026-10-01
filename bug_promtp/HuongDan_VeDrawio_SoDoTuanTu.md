# Hướng dẫn vẽ Sơ đồ tuần tự bằng draw.io — Astraea Eyewear

File này hướng dẫn **từng thao tác trong draw.io** để vẽ các sơ đồ tuần tự cho
Chương 3 của báo cáo. Mỗi sơ đồ có sẵn: tên các cột, nội dung từng mũi tên, loại
mũi tên, **tọa độ (x, y)** để đặt cho thẳng hàng, và vị trí các khung alt/loop/opt.
Bạn chỉ cần làm theo từ trên xuống.

Nội dung đã được phân tích lại trực tiếp từ mã nguồn (`accounts/views.py`,
`accounts/forms.py`, `cart/views.py`, `orders/views.py`, `orders/admin.py`,
`reviews/views.py`, `reviews/ml/sentiment.py`, `tryon/consumers.py`,
`static/js/tryon.js`) — xem mục 1.

---

## Mục lục

1. Phân tích lại: hệ thống chạy thế nào, cần vẽ sơ đồ nào
2. Kiến thức tối thiểu về sơ đồ tuần tự
3. Chuẩn bị draw.io (làm 1 lần)
4. Bộ "khuôn" dùng chung: kích thước, tọa độ, style
5. Vẽ mẫu từng bước: Hình 3.3 Đăng nhập
6. Các sơ đồ còn lại (bảng tọa độ)
7. Xuất ảnh và chèn vào Word
8. Danh sách kiểm tra trước khi nộp

---

## 1. Phân tích lại

### 1.1. Mô hình chung của mọi chức năng

Website viết bằng Django theo mô hình **MVT**. Khi người dùng bấm một nút, luôn
diễn ra cùng một chuỗi:

```
Người dùng ──bấm──▶ Trang web (template) ──gửi yêu cầu──▶ Hàm view (bộ điều khiển)
                                                              │
                                        đọc/ghi ◀────────────┤────────────▶ Cơ sở dữ liệu MySQL
                                                              │
Người dùng ◀──xem── Trang web ◀──── chuyển trang + thông báo ─┘
```

Vì vậy mọi sơ đồ tuần tự trong đồ án dùng chung **4 cột cơ bản**:

| Cột | Tương ứng trong code | Biểu tượng UML |
|---|---|---|
| Khách hàng / Quản trị viên | người dùng | Actor (người que) |
| Giao diện … | file HTML trong `templates/` | Boundary |
| Bộ điều khiển … | hàm view trong `views.py` | Control |
| Cơ sở dữ liệu | MySQL (các bảng User, Cart, Order…) | Entity |

Chỉ hai chức năng AI mới cần **thêm cột thứ 5** để thể hiện phần xử lý thông minh:
- Đánh giá sản phẩm → cột **Mô hình phân loại cảm xúc** (`reviews/ml/sentiment.py`).
- Thử kính ảo → cột **Mô-đun xử lý ảnh** (MediaPipe + OpenCV trong `tryon/`).

### 1.2. Kết quả đối chiếu từng chức năng với code

| Chức năng | Code thực tế làm gì (tóm tắt) | Điểm cần thể hiện trên sơ đồ |
|---|---|---|
| Đăng nhập | Kiểm tra tên đăng nhập + mật khẩu + tài khoản còn hoạt động; đúng thì đăng nhập, **gộp giỏ hàng khách vãng lai**; admin thì vào trang quản trị | 1 khung **alt** (sai / đúng) |
| Đăng ký | Kiểm tra tên đăng nhập trùng, email bắt buộc, mật khẩu đủ mạnh và 2 lần nhập khớp. **Không** kiểm tra email trùng. Lưu tài khoản → tự tạo Ví, Giỏ hàng, Yêu thích → tự đăng nhập → gộp giỏ khách | 1 khung **alt** |
| Tìm kiếm | Lọc sản phẩm đang bán theo tên, mô tả, tên danh mục; không có thì hiện "Không tìm thấy sản phẩm nào…" | 1 khung **alt** |
| Thêm vào giỏ | Lấy sản phẩm; hết hàng thì báo lỗi; còn hàng thì lấy giỏ (theo tài khoản, hoặc theo phiên nếu chưa đăng nhập), cộng dồn số lượng nhưng **không vượt tồn kho** | 1 khung **alt** |
| Đặt hàng | Kiểm tra lần lượt: giỏ trống, tồn kho, hình thức thanh toán, đơn vị vận chuyển, thông tin người nhận. Hợp lệ thì trong **một giao dịch**: tạo đơn → lặp từng sản phẩm lưu chi tiết đơn + trừ kho → xoá giỏ. Thanh toán là **giả lập** | **alt** + **loop** + ghi chú "giao dịch" |
| Đánh giá | Chỉ dòng sản phẩm của **đơn đã giao** và **chưa đánh giá**; form phải có số sao và nội dung; gọi mô hình AI gán nhãn Tích cực/Trung lập/Tiêu cực; lưu đánh giá; lưu tối đa 5 ảnh/video | **alt** + **opt**, thêm cột AI |
| Thử kính ảo | Trình duyệt xin quyền camera → mở WebSocket → chọn mẫu kính (server đọc ảnh PNG từ CSDL) → lặp gửi khung hình ~40 ms/lần → server nhận diện mắt, làm mượt, dán kính, trả ảnh + cờ có/không có mặt | **alt** + **loop**, thêm cột xử lý ảnh |
| Huỷ đơn (tuỳ chọn) | Đơn đã huỷ thì báo lỗi; chưa thì đổi trạng thái + hoàn tồn kho từng sản phẩm trong một giao dịch | **alt** + **loop** |
| Admin cập nhật giao hàng (tuỳ chọn) | Trang quản trị Django; mọi trường của đơn **chỉ đọc**, chỉ sửa được "Trạng thái giao hàng"; không cho tạo đơn mới | không cần khung |

### 1.3. Danh sách hình sẽ vẽ

Báo cáo hiện **chưa có** sơ đồ tuần tự. Thêm mục **3.6. Sơ đồ tuần tự** sau mục 3.5:

| Hình | Tên | Số cột | Ưu tiên |
|---|---|---|---|
| 3.3 | Sơ đồ tuần tự chức năng Đăng nhập | 4 | Bắt buộc |
| 3.4 | Sơ đồ tuần tự chức năng Đăng ký | 4 | Nên có |
| 3.5 | Sơ đồ tuần tự chức năng Tìm kiếm sản phẩm | 4 | Nên có |
| 3.6 | Sơ đồ tuần tự chức năng Thêm sản phẩm vào giỏ hàng | 4 | Bắt buộc |
| 3.7 | Sơ đồ tuần tự chức năng Đặt hàng và thanh toán | 4 | Bắt buộc |
| 3.8 | Sơ đồ tuần tự chức năng Đánh giá sản phẩm và phân loại cảm xúc | 5 | Bắt buộc |
| 3.9 | Sơ đồ tuần tự chức năng Thử kính ảo | 5 | Bắt buộc |
| 3.10 | Sơ đồ tuần tự chức năng Huỷ đơn hàng | 4 | Tuỳ chọn |
| 3.11 | Sơ đồ tuần tự chức năng Cập nhật trạng thái giao hàng | 4 | Tuỳ chọn |

---

## 2. Kiến thức tối thiểu về sơ đồ tuần tự

Chỉ cần nhớ 5 thứ:

| Thành phần | Hình dạng | Ý nghĩa |
|---|---|---|
| **Lifeline (cột)** | Hộp tên + đường nét đứt thẳng đứng | Một đối tượng tham gia |
| **Mũi tên gọi** | Nét **liền**, đầu **tam giác đặc** ▶ | Gửi yêu cầu |
| **Mũi tên trả về** | Nét **đứt**, đầu **mở** > | Trả kết quả |
| **Tự gọi** | Mũi tên đi ra rồi vòng lại chính cột đó | Tự xử lý/kiểm tra |
| **Khung (fragment)** | Hình chữ nhật có nhãn ở góc trái trên | `alt`: rẽ nhánh · `loop`: lặp · `opt`: có thể có hoặc không |

**Đọc sơ đồ:** từ trên xuống dưới là thời gian trôi qua. Mũi tên đánh số 1, 2, 3…
theo đúng thứ tự xảy ra.

**Ba luật không được sai:**
1. Actor chỉ nói chuyện với **Giao diện**.
2. Giao diện không gọi thẳng Cơ sở dữ liệu — phải qua **Bộ điều khiển**.
3. Mọi mũi tên **trả về** đều là nét đứt.

---

## 3. Chuẩn bị draw.io (làm 1 lần)

1. Mở https://app.diagrams.net (hoặc draw.io Desktop) → **Create New Diagram**
   → **Blank Diagram** → đặt tên `Astraea_SequenceDiagrams` → Create.
2. **Bật thư viện UML:** bấm **+ More Shapes** (góc dưới trái) → tick **UML**
   → **Apply**. Bên trái sẽ có nhóm "UML".
3. **Bật lưới để thẳng hàng:** menu **View** → tick **Grid**. Ở bảng bên phải
   (bấm vào chỗ trống trên trang) đặt **Grid size = 10**.
4. **Khổ trang:** bảng bên phải → **Paper size: A4**, chọn **Landscape**
   (nằm ngang) vì sơ đồ rộng.
5. **Mỗi sơ đồ một trang:** bấm dấu **+** ở thanh trang phía dưới để thêm trang,
   nhấp đúp tên trang để đổi thành `3.3 Dang nhap`, `3.4 Dang ky`…
6. **Phông chữ:** chọn tất cả (Ctrl+A) → tab **Text** bên phải → Font
   **Times New Roman**, cỡ **12** (khớp phông của báo cáo). Làm lại bước này
   sau khi vẽ xong mỗi trang.

> **Mẹo:** bấm vào một hình → bảng bên phải có tab **Arrange** — ở đây gõ trực
> tiếp **Left (x), Top (y), Width, Height**. Toàn bộ tọa độ trong file này dùng
> các ô đó.

---

## 4. Bộ "khuôn" dùng chung

### 4.1. Vị trí các cột (lifeline)

Mọi cột: **Width = 120**, phần đầu (hộp tên) cao khoảng 50, **Top (y) = 40**.
Chiều cao (Height) mỗi sơ đồ ghi riêng ở mục 6 (chiều cao này tính cả đường nét đứt).

| Cột thứ | Left (x) | Tâm cột (x) |
|---|---|---|
| 1 | 40 | 100 |
| 2 | 260 | 320 |
| 3 | 480 | 540 |
| 4 | 700 | 760 |
| 5 | 920 | 980 |

Các cột cách nhau 220 px, đủ chỗ cho nhãn mũi tên. Nhãn dài hơn khoảng 35 ký tự
thì bấm **Shift+Enter** để xuống dòng.

### 4.2. Lấy hình ở đâu

Gõ vào ô **Search Shapes** (trên cùng bên trái) rồi kéo hình ra trang:

| Cần vẽ | Gõ tìm | Chọn hình |
|---|---|---|
| Cột Actor | `actor lifeline` | Lifeline có đầu là người que |
| Cột Giao diện | `boundary lifeline` | Lifeline có hình tròn + vạch đứng bên trái |
| Cột Bộ điều khiển | `control lifeline` | Lifeline có hình tròn + mũi tên ở đỉnh |
| Cột CSDL | `entity lifeline` | Lifeline có hình tròn + gạch ngang ở đáy |
| Cột Mô hình AI / Xử lý ảnh | `lifeline` | Lifeline thường (hộp chữ nhật) |
| Mũi tên gọi | `message` | Mũi tên nét liền, đầu đặc |
| Mũi tên trả về | `return` | Mũi tên nét đứt |
| Khung alt/loop/opt | `frame` | Khung có tab nhỏ ở góc trái trên |
| Ghi chú | `note` | Tờ giấy gấp góc |

### 4.3. Style để dán (dùng khi không tìm thấy hình, hoặc muốn sửa cho đồng bộ)

Cách dùng: chọn hình → chuột phải → **Edit Style** (Ctrl+E) → xoá hết → dán
dòng tương ứng → **Apply**.

**Cột Actor**
```
shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;verticalAlign=top;spacingTop=36;outlineConnect=0;portConstraint=eastwest;size=50;fontFamily=Times New Roman;fontSize=12;
```
**Cột Giao diện** (Boundary) — thay `umlActor` bằng `umlBoundary`.
**Cột Bộ điều khiển** (Control) — thay bằng `umlControl`.
**Cột Cơ sở dữ liệu** (Entity) — thay bằng `umlEntity`.

**Cột thường** (Mô hình AI / Xử lý ảnh)
```
shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;portConstraint=eastwest;size=50;fontFamily=Times New Roman;fontSize=12;
```

**Mũi tên gọi**
```
html=1;verticalAlign=bottom;endArrow=block;endFill=1;rounded=0;fontFamily=Times New Roman;fontSize=11;
```

**Mũi tên trả về**
```
html=1;verticalAlign=bottom;endArrow=open;endFill=0;dashed=1;endSize=8;rounded=0;fontFamily=Times New Roman;fontSize=11;
```

**Mũi tên tự gọi**
```
html=1;align=left;spacingLeft=4;endArrow=block;endFill=1;rounded=0;edgeStyle=orthogonalEdgeStyle;fontFamily=Times New Roman;fontSize=11;
```

**Khung alt / loop / opt**
```
shape=umlFrame;whiteSpace=wrap;html=1;pointerEvents=0;width=50;height=22;fillColor=none;fontFamily=Times New Roman;fontSize=12;fontStyle=1;
```

**Đường chia 2 nhánh trong khung alt**
```
endArrow=none;dashed=1;html=1;
```

**Chữ điều kiện `[…]`** — dùng hình **Text** (gõ `text` để tìm):
```
text;html=1;align=left;verticalAlign=middle;fontFamily=Times New Roman;fontSize=11;fontStyle=2;
```

### 4.4. Cách nối mũi tên cho thẳng

1. Kéo hình **message** ra trang.
2. Kéo **đầu đuôi** (chấm tròn ở gốc mũi tên) thả lên **đường nét đứt** của cột
   xuất phát — khi cột hiện viền xanh là đã dính.
3. Kéo **đầu mũi tên** thả lên đường nét đứt của cột đích, **cùng độ cao**
   (tọa độ y ghi trong bảng; nhìn thước dọc bên trái hoặc đếm ô lưới: 1 ô = 10 px).
4. Nếu mũi tên hơi xiên: chọn từng đầu mút, dùng phím **↑ ↓** để nhích.
5. Bấm đúp lên mũi tên → gõ nhãn, ví dụ `1: Nhập tên đăng nhập, mật khẩu`.

**Mũi tên tự gọi:** nối đầu đuôi và đầu mũi tên vào **cùng một cột** — đầu đuôi
ở y ghi trong bảng, đầu mũi tên thấp hơn 30 px. Draw.io tự tạo đường gấp khúc
lòi sang phải; nếu chưa có, kéo điểm giữa đường sang phải khoảng 40 px.

### 4.5. Cách vẽ khung alt

```
 x ─────────────────────────────────────────────┐
 ┌─────┐                                          │  ← Top (y) của khung
 │ alt │ [Sai thông tin]                          │  ← chữ điều kiện nhánh 1
 └─────┘                                          │
        ───── các mũi tên nhánh 1 ─────           │
 - - - - - - - - - - - - - - - - - - - - - - - - -│  ← đường chia (nét đứt)
   [Đúng thông tin]                               │  ← chữ điều kiện nhánh 2
        ───── các mũi tên nhánh 2 ─────           │
 └────────────────────────────────────────────────┘  ← đáy khung
```

1. Kéo hình **frame** ra, gõ tọa độ Left/Top/Width/Height theo bảng.
2. Bấm đúp tab góc trái → gõ `alt` (hoặc `loop`, `opt`).
3. Kéo hình **Text** đặt ngay dưới tab → gõ điều kiện nhánh 1, ví dụ `[Sai thông tin]`.
4. Vẽ đường nét đứt ngang ở tọa độ **"Đường chia"** trong bảng, dài bằng
   chiều rộng khung.
5. Đặt Text điều kiện nhánh 2 ngay dưới đường chia.
6. Chuột phải lên khung → **To Back** để khung nằm dưới mũi tên, không che chữ.

---

## 5. Vẽ mẫu từng bước: Hình 3.3 Đăng nhập

Hình này làm chi tiết từng thao tác. Các hình sau làm y hệt, chỉ khác bảng số liệu.

### Bước 1 — Đặt 4 cột

| Cột | Hình | Tên ghi trong hộp | Left | Top | Width | Height |
|---|---|---|---|---|---|---|
| 1 | Actor | Khách hàng | 40 | 40 | 120 | 650 |
| 2 | Boundary | Giao diện đăng nhập | 260 | 40 | 120 | 650 |
| 3 | Control | Bộ điều khiển đăng nhập | 480 | 40 | 120 | 650 |
| 4 | Entity | Cơ sở dữ liệu | 700 | 40 | 120 | 650 |

### Bước 2 — Vẽ mũi tên theo thứ tự

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Khách hàng → Giao diện | Gọi | 1: Nhập tên đăng nhập, mật khẩu |
| 2 | 190 | Giao diện → Bộ điều khiển | Gọi | 2: Gửi yêu cầu đăng nhập |
| 3 | 240 | Bộ điều khiển → CSDL | Gọi | 3: Tìm tài khoản theo tên đăng nhập |
| 4 | 290 | CSDL → Bộ điều khiển | Trả về | 4: Thông tin tài khoản |
| 5 | 340 | Bộ điều khiển → chính nó | Tự gọi | 5: Kiểm tra mật khẩu, tài khoản còn hoạt động |
| 6 | 450 | Bộ điều khiển → Giao diện | Trả về | 6: Báo lỗi sai tên đăng nhập hoặc mật khẩu |
| 7 | 520 | Bộ điều khiển → CSDL | Gọi | 7: Lưu phiên đăng nhập, gộp giỏ hàng khách vãng lai |
| 8 | 570 | Bộ điều khiển → Giao diện | Trả về | 8: Chuyển về trang chủ (quản trị viên → trang quản trị) |
| 9 | 640 | Giao diện → Khách hàng | Trả về | 9: Hiển thị kết quả |

### Bước 3 — Khung alt

| Thành phần | Left | Top | Width | Height | Nội dung |
|---|---|---|---|---|---|
| Khung | 240 | 400 | 600 | 200 | `alt` |
| Điều kiện nhánh 1 | 300 | 402 | — | — | `[Sai thông tin]` |
| Đường chia | từ x=240 đến x=840 | y=480 | | | nét đứt |
| Điều kiện nhánh 2 | 250 | 485 | — | — | `[Đúng thông tin]` |

Khung bao mũi tên 6 (nhánh trên) và mũi tên 7, 8 (nhánh dưới).

### Bước 4 — Kết quả mong đợi (phác thảo)

```
 Khách hàng    Giao diện ĐN     Bộ điều khiển ĐN     Cơ sở dữ liệu
     |               |                  |                   |
     |--1: Nhập----->|                  |                   |
     |               |--2: Gửi YC------>|                   |
     |               |                  |--3: Tìm TK------->|
     |               |                  |<- - 4: TT TK - - -|
     |               |                  |--.                |
     |               |                  |<-' 5: Kiểm tra MK |
     |          ┌alt─┼──────────────────┼───────────────────┼─┐
     |          │[Sai thông tin]        |                   | │
     |          │    |<- - 6: Báo lỗi - |                   | │
     |          │- - - - - - - - - - - - - - - - - - - - - - -│
     |          │[Đúng thông tin]       |--7: Lưu phiên---->| │
     |          │    |<- - 8: Chuyển trang                  | │
     |          └────┼──────────────────┼───────────────────┼─┘
     |<- 9: Hiển thị-|                  |                   |
```

### Bước 5 — Tiêu đề

Không cần ghi tiêu đề trong hình (tên hình đặt ở chú thích bên dưới trong Word).

---

## 6. Các sơ đồ còn lại

Quy ước trong các bảng:
- **Gọi** = nét liền, đầu đặc · **Trả về** = nét đứt, đầu mở · **Tự gọi** = vòng về chính cột.
- Tất cả cột: Top = 40, Width = 120, Left theo mục 4.1.
- Nhánh 1 của khung alt luôn là **nhánh lỗi** (ngắn), nhánh 2 là **nhánh thành công**.

---

### Hình 3.4. Đăng ký tài khoản

**Cột** (Height = 750): 1 Actor `Khách hàng` · 2 Boundary `Giao diện đăng ký` ·
3 Control `Bộ điều khiển đăng ký` · 4 Entity `Cơ sở dữ liệu`

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Khách hàng → Giao diện | Gọi | 1: Nhập tên đăng nhập, email, SĐT, địa chỉ, mật khẩu |
| 2 | 190 | Giao diện → Bộ điều khiển | Gọi | 2: Gửi yêu cầu đăng ký |
| 3 | 240 | Bộ điều khiển → CSDL | Gọi | 3: Kiểm tra tên đăng nhập đã tồn tại chưa |
| 4 | 290 | CSDL → Bộ điều khiển | Trả về | 4: Kết quả kiểm tra |
| 5 | 340 | Bộ điều khiển (tự gọi) | Tự gọi | 5: Kiểm tra email, độ mạnh và khớp mật khẩu |
| 6 | 450 | Bộ điều khiển → Giao diện | Trả về | 6: Báo lỗi từng trường |
| 7 | 520 | Bộ điều khiển → CSDL | Gọi | 7: Lưu tài khoản mới (mật khẩu đã mã hoá) |
| 8 | 570 | Bộ điều khiển → CSDL | Gọi | 8: Tự tạo Ví, Giỏ hàng, Danh sách yêu thích |
| 9 | 620 | Bộ điều khiển → CSDL | Gọi | 9: Gộp giỏ hàng khách vãng lai |
| 10 | 670 | Bộ điều khiển → Giao diện | Trả về | 10: Đăng nhập, chuyển về trang chủ |
| 11 | 740 | Giao diện → Khách hàng | Trả về | 11: Hiển thị lời chào mừng |

| Khung | Left | Top | Width | Height | Đường chia y | Nhánh 1 | Nhánh 2 |
|---|---|---|---|---|---|---|---|
| alt | 240 | 400 | 600 | 300 | 480 | `[Không hợp lệ]` | `[Hợp lệ]` |

---

### Hình 3.5. Tìm kiếm sản phẩm

**Cột** (Height = 520): 1 Actor `Khách hàng` · 2 Boundary `Giao diện tìm kiếm` ·
3 Control `Bộ điều khiển sản phẩm` · 4 Entity `Cơ sở dữ liệu`

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Khách hàng → Giao diện | Gọi | 1: Nhập từ khoá, bấm Tìm |
| 2 | 190 | Giao diện → Bộ điều khiển | Gọi | 2: Gửi từ khoá tìm kiếm |
| 3 | 240 | Bộ điều khiển → CSDL | Gọi | 3: Tìm sản phẩm đang bán theo tên, mô tả, danh mục |
| 4 | 290 | CSDL → Bộ điều khiển | Trả về | 4: Danh sách sản phẩm |
| 5 | 370 | Bộ điều khiển → Giao diện | Trả về | 5: Danh sách sản phẩm tìm được |
| 6 | 440 | Bộ điều khiển → Giao diện | Trả về | 6: Thông báo không tìm thấy sản phẩm |
| 7 | 510 | Giao diện → Khách hàng | Trả về | 7: Hiển thị kết quả |

| Khung | Left | Top | Width | Height | Đường chia y | Nhánh 1 | Nhánh 2 |
|---|---|---|---|---|---|---|---|
| alt | 240 | 320 | 380 | 150 | 400 | `[Có kết quả]` | `[Không có kết quả]` |

(Khung chỉ rộng từ cột 2 đến cột 3 vì các mũi tên bên trong không chạm CSDL.)

---

### Hình 3.6. Thêm sản phẩm vào giỏ hàng

**Cột** (Height = 670): 1 Actor `Khách hàng` · 2 Boundary `Giao diện chi tiết sản phẩm` ·
3 Control `Bộ điều khiển giỏ hàng` · 4 Entity `Cơ sở dữ liệu`

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Khách hàng → Giao diện | Gọi | 1: Chọn số lượng, bấm Thêm vào giỏ |
| 2 | 190 | Giao diện → Bộ điều khiển | Gọi | 2: Gửi yêu cầu thêm vào giỏ |
| 3 | 240 | Bộ điều khiển → CSDL | Gọi | 3: Lấy thông tin sản phẩm, tồn kho |
| 4 | 290 | CSDL → Bộ điều khiển | Trả về | 4: Thông tin sản phẩm |
| 5 | 370 | Bộ điều khiển → Giao diện | Trả về | 5: Báo sản phẩm đã hết hàng |
| 6 | 440 | Bộ điều khiển → CSDL | Gọi | 6: Lấy giỏ hàng (theo tài khoản hoặc phiên khách) |
| 7 | 490 | CSDL → Bộ điều khiển | Trả về | 7: Giỏ hàng |
| 8 | 540 | Bộ điều khiển → CSDL | Gọi | 8: Thêm sản phẩm hoặc cộng dồn số lượng |
| 9 | 590 | Bộ điều khiển → Giao diện | Trả về | 9: Chuyển tới giỏ hàng, báo thêm thành công |
| 10 | 660 | Giao diện → Khách hàng | Trả về | 10: Hiển thị giỏ hàng |

| Khung | Left | Top | Width | Height | Đường chia y | Nhánh 1 | Nhánh 2 |
|---|---|---|---|---|---|---|---|
| alt | 240 | 320 | 600 | 300 | 400 | `[Hết hàng]` | `[Còn hàng]` |

Ghi chú (tuỳ chọn, hình **note** đặt tại Left 860, Top 520, 170×60):
`Số lượng trong giỏ không vượt quá tồn kho`.

---

### Hình 3.7. Đặt hàng và thanh toán

**Cột** (Height = 810): 1 Actor `Khách hàng` · 2 Boundary `Giao diện giỏ hàng` ·
3 Control `Bộ điều khiển đơn hàng` · 4 Entity `Cơ sở dữ liệu`

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Khách hàng → Giao diện | Gọi | 1: Chọn thanh toán, vận chuyển, nhập người nhận |
| 2 | 190 | Giao diện → Bộ điều khiển | Gọi | 2: Gửi yêu cầu đặt hàng |
| 3 | 240 | Bộ điều khiển → CSDL | Gọi | 3: Lấy giỏ hàng và các sản phẩm |
| 4 | 290 | CSDL → Bộ điều khiển | Trả về | 4: Danh sách sản phẩm trong giỏ |
| 5 | 340 | Bộ điều khiển (tự gọi) | Tự gọi | 5: Kiểm tra giỏ, tồn kho, thanh toán, vận chuyển, người nhận |
| 6 | 450 | Bộ điều khiển → Giao diện | Trả về | 6: Báo lỗi, giữ nguyên giỏ hàng |
| 7 | 520 | Bộ điều khiển → CSDL | Gọi | 7: Tạo đơn hàng |
| 8 | 610 | Bộ điều khiển → CSDL | Gọi | 8: Lưu chi tiết đơn (giá lúc mua), trừ tồn kho |
| 9 | 680 | Bộ điều khiển → CSDL | Gọi | 9: Xoá giỏ hàng |
| 10 | 730 | Bộ điều khiển → Giao diện | Trả về | 10: Chuyển tới Đơn hàng của tôi, báo thành công |
| 11 | 800 | Giao diện → Khách hàng | Trả về | 11: Hiển thị đơn vừa đặt |

| Khung | Left | Top | Width | Height | Đường chia y | Nhánh 1 | Nhánh 2 |
|---|---|---|---|---|---|---|---|
| alt | 240 | 400 | 600 | 360 | 480 | `[Không hợp lệ]` | `[Hợp lệ]` |
| loop (nằm trong alt) | 460 | 550 | 380 | 90 | — | `[Mỗi sản phẩm trong giỏ]` | — |

Ghi chú (**note** tại Left 860, Top 500, 180×90):
`Bước 7–9 thực hiện trong một giao dịch: lỗi giữa chừng thì huỷ toàn bộ. Thanh toán là giả lập.`
Nối note với khung alt bằng một đường nét đứt không mũi tên (style: `endArrow=none;dashed=1;html=1;`).

---

### Hình 3.8. Đánh giá sản phẩm và phân loại cảm xúc

**Cột** (Height = 840): 1 Actor `Khách hàng` · 2 Boundary `Giao diện chi tiết sản phẩm` ·
3 Control `Bộ điều khiển đánh giá` · 4 Lifeline thường `Mô hình phân loại cảm xúc` ·
5 Entity `Cơ sở dữ liệu`

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Khách hàng → Giao diện | Gọi | 1: Chọn số sao, nhập nội dung, đính kèm ảnh/video |
| 2 | 190 | Giao diện → Bộ điều khiển | Gọi | 2: Gửi đánh giá |
| 3 | 240 | Bộ điều khiển → CSDL | Gọi | 3: Kiểm tra đơn đã giao, sản phẩm chưa được đánh giá |
| 4 | 290 | CSDL → Bộ điều khiển | Trả về | 4: Kết quả kiểm tra |
| 5 | 370 | Bộ điều khiển → Giao diện | Trả về | 5: Báo lỗi |
| 6 | 440 | Bộ điều khiển → Mô hình | Gọi | 6: Gửi nội dung bình luận |
| 7 | 490 | Mô hình (tự gọi) | Tự gọi | 7: Làm sạch, tách từ, TF-IDF, Logistic Regression |
| 8 | 550 | Mô hình → Bộ điều khiển | Trả về | 8: Nhãn cảm xúc + độ tin cậy |
| 9 | 600 | Bộ điều khiển → CSDL | Gọi | 9: Lưu đánh giá kèm nhãn cảm xúc |
| 10 | 690 | Bộ điều khiển → CSDL | Gọi | 10: Lưu ảnh/video đính kèm (tối đa 5) |
| 11 | 760 | Bộ điều khiển → Giao diện | Trả về | 11: Hiển thị đánh giá kèm nhãn cảm xúc |
| 12 | 830 | Giao diện → Khách hàng | Trả về | 12: Xem đánh giá vừa gửi |

Mũi tên 3, 9, 10 đi **xuyên qua** cột Mô hình để tới CSDL — bình thường, không nối vào cột Mô hình.

| Khung | Left | Top | Width | Height | Đường chia y | Nhánh 1 | Nhánh 2 |
|---|---|---|---|---|---|---|---|
| alt | 240 | 320 | 820 | 470 | 400 | `[Chưa giao / đã đánh giá / thiếu sao hoặc nội dung]` | `[Đủ điều kiện]` |
| opt (nằm trong alt) | 460 | 630 | 600 | 90 | — | `[Có ảnh/video]` | — |

Ghi chú (tuỳ chọn, **note** tại Left 1080, Top 440, 180×80):
`Nhãn: Tích cực / Trung lập / Tiêu cực. Mô hình đã huấn luyện sẵn (sentiment_model.joblib).`

---

### Hình 3.9. Thử kính ảo

**Cột** (Height = 960): 1 Actor `Khách hàng` · 2 Boundary `Cửa sổ thử kính` ·
3 Control `Máy chủ xử lý (WebSocket)` · 4 Lifeline thường `Mô-đun xử lý ảnh (MediaPipe, OpenCV)` ·
5 Entity `Cơ sở dữ liệu`

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Khách hàng → Cửa sổ | Gọi | 1: Bấm Thử kính |
| 2 | 190 | Cửa sổ (tự gọi) | Tự gọi | 2: Xin quyền mở webcam |
| 3 | 300 | Cửa sổ → Khách hàng | Trả về | 3: Báo không mở được camera |
| 4 | 370 | Cửa sổ → Máy chủ | Gọi | 4: Mở kết nối WebSocket |
| 5 | 420 | Cửa sổ → Máy chủ | Gọi | 5: Gửi mẫu kính đã chọn |
| 6 | 470 | Máy chủ → CSDL | Gọi | 6: Lấy ảnh kính (PNG) và thông số |
| 7 | 520 | CSDL → Máy chủ | Trả về | 7: Ảnh kính |
| 8 | 610 | Cửa sổ → Máy chủ | Gọi | 8: Gửi khung hình webcam (JPEG) |
| 9 | 660 | Máy chủ → Mô-đun xử lý ảnh | Gọi | 9: Nhận diện mắt, làm mượt, dán kính |
| 10 | 710 | Mô-đun xử lý ảnh → Máy chủ | Trả về | 10: Khung hình đã ghép kính |
| 11 | 760 | Máy chủ → Cửa sổ | Trả về | 11: Trả khung hình + cờ có/không có mặt |
| 12 | 810 | Cửa sổ → Khách hàng | Trả về | 12: Hiển thị hình đeo kính |
| 13 | 880 | Khách hàng → Cửa sổ | Gọi | 13: Đóng cửa sổ |
| 14 | 930 | Cửa sổ → Máy chủ | Gọi | 14: Ngắt kết nối, tắt camera |

| Khung | Left | Top | Width | Height | Đường chia y | Nhánh 1 | Nhánh 2 |
|---|---|---|---|---|---|---|---|
| alt | 20 | 250 | 1040 | 710 | 330 | `[Từ chối camera]` | `[Cho phép]` |
| loop (nằm trong alt) | 40 | 560 | 1000 | 280 | — | `[Mỗi khung hình, khoảng 40 ms/lần]` | — |

Ghi chú (**note** tại Left 1080, Top 620, 190×110):
`Mất khuôn mặt từ 3 khung liên tiếp: trả ảnh gốc với cờ = 0, cửa sổ hiện "Không phát hiện khuôn mặt".`

> Khung alt ở hình này bắt đầu từ x = 20 để bao được cả cột Khách hàng (vì mũi
> tên 3, 12, 13 chạm cột Khách hàng).

---

### Hình 3.10 (tuỳ chọn). Huỷ đơn hàng

**Cột** (Height = 680): 1 Actor `Khách hàng` · 2 Boundary `Giao diện đơn hàng của tôi` ·
3 Control `Bộ điều khiển đơn hàng` · 4 Entity `Cơ sở dữ liệu`

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Khách hàng → Giao diện | Gọi | 1: Bấm Huỷ đơn |
| 2 | 190 | Giao diện → Bộ điều khiển | Gọi | 2: Gửi yêu cầu huỷ đơn |
| 3 | 240 | Bộ điều khiển → CSDL | Gọi | 3: Lấy đơn hàng của người dùng |
| 4 | 290 | CSDL → Bộ điều khiển | Trả về | 4: Thông tin đơn hàng |
| 5 | 370 | Bộ điều khiển → Giao diện | Trả về | 5: Báo đơn đã được huỷ từ trước |
| 6 | 440 | Bộ điều khiển → CSDL | Gọi | 6: Đổi trạng thái đơn thành Đã huỷ |
| 7 | 530 | Bộ điều khiển → CSDL | Gọi | 7: Cộng lại tồn kho sản phẩm |
| 8 | 600 | Bộ điều khiển → Giao diện | Trả về | 8: Báo huỷ đơn thành công |
| 9 | 670 | Giao diện → Khách hàng | Trả về | 9: Hiển thị danh sách đơn đã cập nhật |

| Khung | Left | Top | Width | Height | Đường chia y | Nhánh 1 | Nhánh 2 |
|---|---|---|---|---|---|---|---|
| alt | 240 | 320 | 600 | 310 | 400 | `[Đơn đã huỷ từ trước]` | `[Đơn chưa huỷ]` |
| loop (nằm trong alt) | 460 | 470 | 380 | 90 | — | `[Mỗi sản phẩm trong đơn]` | — |

---

### Hình 3.11 (tuỳ chọn). Quản trị viên cập nhật trạng thái giao hàng

**Cột** (Height = 600): 1 Actor `Quản trị viên` · 2 Boundary `Giao diện trang quản trị` ·
3 Control `Bộ điều khiển quản trị` · 4 Entity `Cơ sở dữ liệu`

| # | y | Từ → Đến | Loại | Nhãn |
|---|---|---|---|---|
| 1 | 140 | Quản trị viên → Giao diện | Gọi | 1: Mở mục Đơn hàng |
| 2 | 190 | Giao diện → Bộ điều khiển | Gọi | 2: Yêu cầu danh sách đơn hàng |
| 3 | 240 | Bộ điều khiển → CSDL | Gọi | 3: Lấy danh sách đơn hàng |
| 4 | 290 | CSDL → Bộ điều khiển | Trả về | 4: Danh sách đơn hàng |
| 5 | 340 | Bộ điều khiển → Giao diện | Trả về | 5: Hiển thị danh sách |
| 6 | 390 | Quản trị viên → Giao diện | Gọi | 6: Chọn đơn, đổi trạng thái giao hàng, bấm Lưu |
| 7 | 440 | Giao diện → Bộ điều khiển | Gọi | 7: Gửi trạng thái giao hàng mới |
| 8 | 490 | Bộ điều khiển → CSDL | Gọi | 8: Cập nhật trạng thái giao hàng |
| 9 | 540 | Bộ điều khiển → Giao diện | Trả về | 9: Báo lưu thành công |
| 10 | 590 | Giao diện → Quản trị viên | Trả về | 10: Hiển thị thông báo |

Không có khung. Ghi chú (**note** tại Left 860, Top 380, 180×80):
`Các trường khác của đơn chỉ đọc; không cho tạo đơn mới từ trang quản trị.`

---

## 7. Xuất ảnh và chèn vào Word

1. Chọn trang cần xuất → **File → Export as → PNG…**
2. Thiết lập: **Zoom 200%** (ảnh nét khi in), **Border width 10**, **bỏ tick
   Transparent Background** (để nền trắng), **Selection only: không tick**.
3. **Export** → đặt tên theo số hình, ví dụ `Hinh_3_7_DatHang.png`.
4. Trong Word, đặt con trỏ ở mục 3.6 → **Insert → Pictures** → chọn ảnh →
   căn giữa, chiều rộng tối đa bằng lề trang (khoảng 16 cm).
5. Dòng dưới ảnh gõ chú thích, ví dụ `Hình 3.7. Sơ đồ tuần tự chức năng Đặt
   hàng và thanh toán`, áp style **"Chu thich hinh"** giống các hình 3.1, 3.2.
6. Trước mỗi hình viết 2–4 câu mô tả: *ai bắt đầu → hệ thống kiểm tra gì →
   nhánh thành công → nhánh lỗi*. Ví dụ cho Hình 3.7:
   > Khi khách hàng xác nhận đặt hàng, bộ điều khiển đơn hàng lấy giỏ hàng và
   > kiểm tra giỏ không trống, đủ tồn kho, đã chọn hình thức thanh toán, đơn vị
   > vận chuyển và nhập đủ thông tin người nhận. Nếu hợp lệ, hệ thống tạo đơn,
   > lưu từng dòng sản phẩm với giá tại thời điểm mua, trừ tồn kho và xoá giỏ
   > hàng trong cùng một giao dịch; ngược lại hệ thống báo lỗi và giữ nguyên giỏ.
7. Chèn xong tất cả hình → chuột phải vào **Danh mục hình vẽ** → **Update
   Field → Update entire table**.

**Lưu file gốc:** File → Save as → lưu `Astraea_SequenceDiagrams.drawio` cùng
thư mục đồ án để sửa lại sau.

---

## 8. Danh sách kiểm tra trước khi nộp

- [ ] Mỗi sơ đồ có đủ cột theo đúng thứ tự Actor → Giao diện → Bộ điều khiển → (AI) → CSDL.
- [ ] Các cột cùng độ cao, cách đều nhau.
- [ ] Mọi mũi tên nằm ngang, được đánh số liên tục 1, 2, 3…
- [ ] Mũi tên trả về là **nét đứt**, mũi tên gọi là **nét liền đầu đặc**.
- [ ] Actor không nối thẳng CSDL; Giao diện không nối thẳng CSDL.
- [ ] Mỗi khung có nhãn `alt` / `loop` / `opt` và điều kiện trong `[ ]`.
- [ ] Khung alt có đường nét đứt chia 2 nhánh.
- [ ] Nhãn tiếng Việt, không chứa tên hàm Python hay câu SQL.
- [ ] Hình Đặt hàng có ghi chú "giao dịch" và "thanh toán giả lập".
- [ ] Phông Times New Roman, cỡ chữ đồng nhất giữa các hình.
- [ ] Số hình và tên hình trong Word khớp với bảng ở mục 1.3.
