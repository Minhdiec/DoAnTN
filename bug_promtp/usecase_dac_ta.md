# Bảng đặc tả use case (mô tả lại theo đúng sơ đồ `usecase .png`)

Đối chiếu ảnh sơ đồ use case với "Bảng 3.1. Bảng đặc tả use case" đang có trong báo cáo: sơ đồ vẽ
7 use case phía Khách hàng + 7 use case phía Quản trị viên (14 tổng), nhưng bảng đặc tả hiện tại
trong `Copy.final.docx` chỉ có 12 dòng và **thiếu hẳn 4 use case phía Quản trị viên** (Quản lí sản
phẩm, Quản lí danh mục, Quản lí giao dịch, Quản lí người dùng), trong khi lại có 2 dòng ("Quên và
đặt lại mật khẩu", "Yêu thích") không xuất hiện trong sơ đồ. Xem mục "Lệch cần quyết định" ở cuối
file.

## Khách hàng

| STT | Use case | Điều kiện trước, sau | Luồng xử lý chính | Ngoại lệ, rẽ nhánh |
|---|---|---|---|---|
| 1 | Đăng nhập/ Đăng ký | Chưa có tài khoản hoặc đã có; sau khi xong thì vào được hệ thống đúng quyền | Đăng ký: nhập username, email, SĐT, địa chỉ, mật khẩu, kiểm tra trùng lặp và độ mạnh, tạo tài khoản, tự đăng nhập, gộp giỏ hàng khách. Đăng nhập: nhập username/mật khẩu, xác thực, gộp giỏ hàng khách, vào trang quản trị nếu là admin | Thiếu trường/mật khẩu yếu báo lỗi từng trường; username/email trùng báo lỗi; sai username hoặc mật khẩu báo lỗi chung, không lộ trường nào sai |
| 2 | Xem và tìm kiếm sản phẩm | Không yêu cầu đăng nhập | Trang chủ liệt kê danh mục và sản phẩm đang bán; ô tìm kiếm lọc theo tên, mô tả, danh mục; trang chi tiết hiển thị ảnh, giá, tồn kho, rating, tỉ lệ cảm xúc, nút thử kính ảo nếu sản phẩm có ảnh AR | Không có |
| 3 | Thử kính ảo `<<Include>>` Nhận diện khuôn mặt và ghép kính | Trình duyệt hỗ trợ WebSocket + camera, sản phẩm có ảnh AR | Mở WebSocket, trình duyệt gửi liên tục khung hình webcam (~25 fps); server dùng MediaPipe phát hiện landmark mắt, lọc mượt bằng One-Euro Filter, dùng OpenCV biến đổi affine + alpha blend để dán kính, trả JPEG kèm cờ có/không phát hiện mặt; đổi mẫu kính ngay trong lúc thử | Mất mặt từ 3 khung liên tiếp: trả khung gốc kèm cảnh báo; từ chối quyền camera: báo lỗi không mở được |
| 4 | Quản lí giỏ hàng | Sản phẩm đang được bán | Thêm sản phẩm vào giỏ (giỏ theo session nếu chưa đăng nhập), đổi số lượng hoặc xoá dòng qua AJAX, cập nhật ngay không tải lại trang | Sản phẩm hết hàng: báo lỗi, không thêm được |
| 5 | Đặt hàng và thanh toán | Giỏ không trống; sau khi xong: đơn được tạo, tồn kho bị trừ, giỏ bị xoá | Nhập thông tin nhận hàng, chọn hình thức thanh toán (COD/MoMo/Thẻ - giả lập, không gọi cổng thanh toán thật) và đơn vị vận chuyển; trong 1 giao dịch atomic: tạo đơn + từng dòng sản phẩm (lưu giá tại thời điểm mua), trừ tồn kho, xoá giỏ, coi như thanh toán và giao thành công ngay | Giỏ trống, sản phẩm vượt tồn kho, hoặc thiếu thông tin nhận hàng: báo lỗi, không tạo đơn |
| 6 | Theo dõi đơn hàng | Đã đăng nhập | Liệt kê đơn của người dùng (mới nhất trước) kèm badge trạng thái giao hàng; huỷ một đơn còn hiệu lực thì đổi trạng thái và hoàn tồn kho từng sản phẩm trong 1 giao dịch | Đơn đã ở trạng thái huỷ từ trước: báo lỗi, không xử lý lại |
| 7 | Đánh giá sản phẩm `<<Include>>` Phân loại cảm xúc bình luận | Đã mua và đơn đã giao, chưa từng đánh giá sản phẩm này | Chọn số sao, nhập nội dung, tuỳ chọn ẩn danh, đính kèm tối đa 5 ảnh/video; hệ thống kiểm tra lại điều kiện đã mua/đã giao/chưa đánh giá, gọi mô hình TF-IDF + Logistic Regression để gán nhãn Tích cực/Trung lập/Tiêu cực, lưu đánh giá | Đơn chưa giao, hoặc đã đánh giá sản phẩm này trước đó: báo lỗi |

## Quản trị viên

| STT | Use case | Điều kiện trước, sau | Luồng xử lý chính | Ngoại lệ, rẽ nhánh |
|---|---|---|---|---|
| 8 | Quản lí sản phẩm | Đăng nhập với quyền is_staff/is_superuser | Thêm/sửa/xoá sản phẩm (tên, danh mục, giá, tồn kho, mô tả, SKU, trạng thái đang bán), quản lý ảnh phụ ngay trong trang chi tiết sản phẩm (inline), lọc theo danh mục/trạng thái, tìm theo tên/mô tả/SKU | Không có |
| 9 | Quản lí danh mục | Đăng nhập với quyền quản trị | Thêm/sửa/xoá danh mục kính theo dáng gọng (Oval, Square...), slug tự sinh từ tên, tìm theo tên | Không có |
| 10 | Quản lí đơn hàng | Đăng nhập với quyền quản trị | Mở chi tiết một đơn (toàn bộ chỉ đọc), chỉ sửa được đúng trường trạng thái giao hàng, lưu, badge cập nhật ngay ở trang khách hàng | Không cho tạo đơn mới trực tiếp từ trang quản trị - đơn chỉ được tạo qua luồng đặt hàng thật |
| 11 | Quản lí giao dịch | Đăng nhập với quyền quản trị | Xem số dư ví và lịch sử giao dịch (nạp/trừ tiền) của từng người dùng, xem chi tiết loại giao dịch, số tiền, số dư sau giao dịch | Không cho thêm/sửa số dư hay giao dịch trực tiếp qua admin - số dư chỉ đổi qua `Wallet.deposit()/withdraw()` để giữ đối soát đúng với lịch sử |
| 12 | Quản lí bình luận và cảm xúc | Đăng nhập với quyền quản trị | Xem danh sách đánh giá kèm nhãn cảm xúc và độ tin cậy, lọc theo sản phẩm/số sao/nhãn cảm xúc, xoá đánh giá vi phạm | Không cho thêm hoặc sửa nội dung/nhãn cảm xúc của đánh giá qua trang quản trị - chỉ được xem và xoá |
| 13 | Thống kê cảm xúc bình luận | Đăng nhập với quyền quản trị | Xem tỉ lệ % Tích cực/Trung lập/Tiêu cực tổng và biểu đồ theo từng sản phẩm, luôn tính lại theo đúng bộ lọc (sản phẩm, số sao) đang áp dụng trên trang | Không có |
| 14 | Quản lí người dùng | Đăng nhập với quyền is_superuser | Xem/sửa thông tin tài khoản (họ tên, email, SĐT, địa chỉ), cấp/thu quyền is_staff, is_superuser, is_active, tìm theo username/email/SĐT | Không hiển thị chi tiết mật khẩu đã băm; không dùng model Group (chỉ phân quyền qua is_staff/is_superuser) |

## Lệch cần quyết định

2 use case cũ trong bảng đặc tả hiện tại của báo cáo không xuất hiện trong sơ đồ:

- **Quên và đặt lại mật khẩu** (Khách vãng lai) - có thật trong code (`accounts/views.py
  forgot_password_view`, `reset_password_view`).
- **Thêm, bỏ sản phẩm yêu thích** (Thành viên) - có thật trong code (app `favorites`).

Giữ nguyên trong bảng đặc tả (bổ sung ghi chú là sơ đồ rút gọn) hay bỏ ra để khớp đúng 14 ô trong
sơ đồ - cần bạn quyết định trước khi cập nhật `Copy.final.docx`.
