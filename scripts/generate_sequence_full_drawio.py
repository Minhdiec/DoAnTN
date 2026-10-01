"""
Sinh file draw.io đủ sơ đồ tuần tự cho TOÀN BỘ chức năng khách hàng + 1 sơ đồ
quản trị viên (Quản lí bình luận và thống kê cảm xúc). Chỉ vẽ luồng chính,
KHÔNG vẽ khung alt/loop/opt. Luồng bám đúng code hiện tại.

Chạy:  .venv\\Scripts\\python.exe scripts\\generate_sequence_full_drawio.py [--preview <thư mục>]
Kết quả: bug_promtp/sodotuantu_daydu.drawio.xml
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_sequence_drawio as base  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "bug_promtp" / "sodotuantu_daydu.drawio.xml"

A, B, C, E, S = base.ACTOR, base.BOUNDARY, base.CONTROL, "Entity / MySQL", base.SERVICE
KH = ("Khách hàng", A)
DB = ("Cơ sở dữ liệu", E)

# (tên trang, các cột, các bước) — bước: (từ, đến, loại, nhãn); loại c=gọi, r=trả về, s=tự gọi
SPECS = [
    ("Hình 3.3 - Đăng ký tài khoản",
     [KH, ("Giao diện đăng ký", B), ("Bộ điều khiển tài khoản", C), DB], [
         (0, 1, "c", "Nhập tên đăng nhập, email, SĐT, địa chỉ, mật khẩu"),
         (1, 2, "c", "Gửi yêu cầu đăng ký"),
         (2, 3, "c", "Kiểm tra tên đăng nhập đã tồn tại"),
         (3, 2, "r", "Kết quả kiểm tra"),
         (2, 2, "s", "Kiểm tra email bắt buộc, độ mạnh và khớp mật khẩu"),
         (2, 3, "c", "Lưu tài khoản mới (mật khẩu đã mã hoá)"),
         (2, 3, "c", "Tự tạo Ví, Giỏ hàng, Danh sách yêu thích"),
         (2, 2, "s", "Tự đăng nhập, khởi tạo phiên"),
         (2, 3, "c", "Gộp giỏ hàng khách vãng lai"),
         (2, 1, "r", "Chuyển về trang chủ, báo chào mừng"),
         (1, 0, "r", "Hiển thị trang chủ"),
     ]),
    ("Hình 3.4 - Đăng nhập",
     [KH, ("Giao diện đăng nhập", B), ("Bộ điều khiển tài khoản", C), DB], [
         (0, 1, "c", "Yêu cầu trang đăng nhập"),
         (1, 0, "r", "Hiển thị form đăng nhập"),
         (0, 1, "c", "Nhập tên đăng nhập, mật khẩu"),
         (1, 2, "c", "Gửi yêu cầu đăng nhập"),
         (2, 3, "c", "Truy vấn tài khoản theo tên đăng nhập"),
         (3, 2, "r", "Thông tin tài khoản"),
         (2, 2, "s", "Xác thực mật khẩu và trạng thái tài khoản"),
         (2, 2, "s", "Khởi tạo phiên đăng nhập"),
         (2, 3, "c", "Lấy giỏ hàng khách theo mã phiên cũ"),
         (3, 2, "r", "Giỏ hàng khách vãng lai"),
         (2, 3, "c", "Gộp sản phẩm vào giỏ tài khoản, xoá giỏ khách"),
         (2, 2, "s", "Chọn trang chuyển tới theo quyền"),
         (2, 1, "r", "Chuyển hướng kèm cookie phiên, báo đăng nhập thành công"),
         (1, 0, "r", "Hiển thị trang chủ / trang quản trị"),
     ]),
    ("Hình 3.5 - Quên và đặt lại mật khẩu",
     [KH, ("Giao diện quên mật khẩu", B), ("Bộ điều khiển tài khoản", C), DB], [
         (0, 1, "c", "Nhập tên đăng nhập, email hoặc SĐT"),
         (1, 2, "c", "Gửi yêu cầu xác minh"),
         (2, 3, "c", "Tìm tài khoản theo tên đăng nhập"),
         (3, 2, "r", "Thông tin tài khoản"),
         (2, 2, "s", "So khớp email/SĐT với hồ sơ"),
         (2, 2, "s", "Lưu xác minh vào phiên (hiệu lực 10 phút)"),
         (2, 1, "r", "Chuyển tới trang đặt mật khẩu mới"),
         (1, 0, "r", "Hiển thị form đặt mật khẩu mới"),
         (0, 1, "c", "Nhập mật khẩu mới hai lần"),
         (1, 2, "c", "Gửi mật khẩu mới"),
         (2, 2, "s", "Kiểm tra phiên còn hạn, mật khẩu hợp lệ"),
         (2, 3, "c", "Cập nhật mật khẩu (đã mã hoá)"),
         (2, 2, "s", "Xoá thông tin xác minh khỏi phiên"),
         (2, 1, "r", "Chuyển tới trang đăng nhập, báo thành công"),
         (1, 0, "r", "Hiển thị trang đăng nhập"),
     ]),
    ("Hình 3.6 - Xem chi tiết sản phẩm",
     [KH, ("Giao diện chi tiết sản phẩm", B), ("Bộ điều khiển sản phẩm", C), DB], [
         (0, 1, "c", "Chọn một sản phẩm"),
         (1, 2, "c", "Yêu cầu xem chi tiết sản phẩm"),
         (2, 3, "c", "Lấy sản phẩm đang bán, ảnh phụ, ảnh kính thử"),
         (3, 2, "r", "Thông tin sản phẩm"),
         (2, 3, "c", "Lấy đánh giá, thống kê số sao và tỉ lệ cảm xúc"),
         (3, 2, "r", "Danh sách đánh giá, số liệu thống kê"),
         (2, 3, "c", "Lấy sản phẩm cùng danh mục"),
         (3, 2, "r", "Sản phẩm liên quan"),
         (2, 1, "r", "Trả trang chi tiết sản phẩm"),
         (1, 0, "r", "Hiển thị ảnh, giá, tồn kho, đánh giá, nút thử kính"),
     ]),
    ("Hình 3.7 - Tìm kiếm sản phẩm",
     [KH, ("Giao diện tìm kiếm", B), ("Bộ điều khiển sản phẩm", C), DB], [
         (0, 1, "c", "Nhập từ khoá, bấm Tìm"),
         (1, 2, "c", "Gửi từ khoá tìm kiếm"),
         (2, 3, "c", "Tìm sản phẩm đang bán theo tên, mô tả, danh mục"),
         (3, 2, "r", "Danh sách sản phẩm"),
         (2, 1, "r", "Trả trang kết quả tìm kiếm"),
         (1, 0, "r", "Hiển thị sản phẩm tìm được"),
     ]),
    ("Hình 3.8 - Thử kính ảo",
     [KH, ("Cửa sổ thử kính", B), ("Máy chủ xử lý (WebSocket)", C),
      ("Mô-đun xử lý ảnh (MediaPipe, OpenCV)", S), DB], [
         (0, 1, "c", "Bấm Thử kính"),
         (1, 1, "s", "Xin quyền mở webcam"),
         (1, 2, "c", "Mở kết nối WebSocket"),
         (2, 3, "c", "Khởi tạo bộ nhận diện khuôn mặt"),
         (1, 2, "c", "Gửi mẫu kính đã chọn"),
         (2, 4, "c", "Lấy thông tin mẫu kính (đường dẫn ảnh PNG)"),
         (4, 2, "r", "Thông tin mẫu kính"),
         (2, 2, "s", "Đọc ảnh kính PNG, xác định tâm tròng kính"),
         (1, 2, "c", "Gửi khung hình webcam JPEG (lặp ~40 ms/lần)"),
         (2, 3, "c", "Nhận diện mắt, làm mượt, dán kính"),
         (3, 2, "r", "Khung hình đã ghép kính"),
         (2, 1, "r", "Khung hình + cờ có/không có khuôn mặt"),
         (1, 0, "r", "Hiển thị hình đeo kính"),
         (0, 1, "c", "Đóng cửa sổ thử kính"),
         (1, 2, "c", "Ngắt kết nối, tắt camera"),
         (2, 3, "c", "Giải phóng bộ nhận diện"),
     ]),
    ("Hình 3.9 - Thêm sản phẩm vào giỏ hàng",
     [KH, ("Giao diện chi tiết sản phẩm", B), ("Bộ điều khiển giỏ hàng", C), DB], [
         (0, 1, "c", "Chọn số lượng, bấm Thêm vào giỏ"),
         (1, 2, "c", "Gửi yêu cầu thêm vào giỏ"),
         (2, 3, "c", "Lấy sản phẩm đang bán, tồn kho"),
         (3, 2, "r", "Thông tin sản phẩm"),
         (2, 2, "s", "Kiểm tra sản phẩm còn hàng"),
         (2, 3, "c", "Lấy giỏ hàng (theo tài khoản hoặc phiên khách)"),
         (3, 2, "r", "Giỏ hàng"),
         (2, 3, "c", "Thêm hoặc cộng dồn số lượng (không vượt tồn kho)"),
         (2, 1, "r", "Chuyển tới giỏ hàng, báo thêm thành công"),
         (1, 0, "r", "Hiển thị giỏ hàng"),
     ]),
    ("Hình 3.10 - Cập nhật và xoá sản phẩm trong giỏ",
     [KH, ("Giao diện giỏ hàng", B), ("Bộ điều khiển giỏ hàng", C), DB], [
         (0, 1, "c", "Đổi số lượng hoặc bấm Xoá"),
         (1, 2, "c", "Gửi yêu cầu cập nhật / xoá (AJAX)"),
         (2, 3, "c", "Lấy giỏ hàng và dòng sản phẩm"),
         (3, 2, "r", "Dòng sản phẩm trong giỏ"),
         (2, 2, "s", "Giới hạn số lượng từ 1 đến tồn kho"),
         (2, 3, "c", "Cập nhật số lượng hoặc xoá dòng sản phẩm"),
         (2, 3, "c", "Tính lại tổng số lượng, tổng tiền"),
         (3, 2, "r", "Tổng số lượng, tổng tiền"),
         (2, 1, "r", "Trả dữ liệu JSON"),
         (1, 1, "s", "Cập nhật giỏ, không tải lại trang"),
         (1, 0, "r", "Hiển thị giỏ hàng mới"),
     ]),
    ("Hình 3.11 - Đặt hàng và thanh toán",
     [KH, ("Giao diện giỏ hàng", B), ("Bộ điều khiển đơn hàng", C), DB], [
         (0, 1, "c", "Chọn thanh toán (giả lập), vận chuyển, nhập người nhận"),
         (1, 2, "c", "Gửi yêu cầu đặt hàng"),
         (2, 3, "c", "Lấy giỏ hàng và các sản phẩm"),
         (3, 2, "r", "Danh sách sản phẩm trong giỏ"),
         (2, 2, "s", "Kiểm tra giỏ trống, tồn kho, thanh toán, vận chuyển, người nhận"),
         (2, 2, "s", "Tính tổng tiền đơn hàng"),
         (2, 3, "c", "Bắt đầu giao dịch, tạo đơn hàng"),
         (2, 3, "c", "Lưu chi tiết đơn (giá lúc mua), trừ tồn kho từng sản phẩm"),
         (2, 3, "c", "Xoá giỏ hàng, kết thúc giao dịch"),
         (2, 1, "r", "Chuyển tới Đơn hàng của tôi, báo thanh toán thành công"),
         (1, 0, "r", "Hiển thị đơn vừa đặt"),
     ]),
    ("Hình 3.12 - Theo dõi và huỷ đơn hàng",
     [KH, ("Giao diện đơn hàng của tôi", B), ("Bộ điều khiển đơn hàng", C), DB], [
         (0, 1, "c", "Mở trang Đơn hàng của tôi"),
         (1, 2, "c", "Yêu cầu danh sách đơn hàng"),
         (2, 3, "c", "Lấy đơn của người dùng (mới nhất trước)"),
         (3, 2, "r", "Danh sách đơn và sản phẩm trong đơn"),
         (2, 3, "c", "Lấy các sản phẩm đã đánh giá"),
         (3, 2, "r", "Danh sách sản phẩm đã đánh giá"),
         (2, 1, "r", "Trả danh sách đơn kèm trạng thái giao hàng"),
         (1, 0, "r", "Hiển thị đơn hàng, trạng thái giao hàng"),
         (0, 1, "c", "Bấm Huỷ đơn"),
         (1, 2, "c", "Gửi yêu cầu huỷ đơn"),
         (2, 3, "c", "Lấy đơn hàng của người dùng"),
         (3, 2, "r", "Thông tin đơn hàng"),
         (2, 2, "s", "Kiểm tra đơn chưa bị huỷ"),
         (2, 3, "c", "Đổi trạng thái đơn thành Đã huỷ"),
         (2, 3, "c", "Cộng lại tồn kho từng sản phẩm"),
         (2, 1, "r", "Chuyển về Đơn hàng của tôi, báo huỷ thành công"),
         (1, 0, "r", "Hiển thị đơn đã huỷ"),
     ]),
    ("Hình 3.13 - Đánh giá sản phẩm và phân loại cảm xúc",
     [KH, ("Giao diện chi tiết sản phẩm", B), ("Bộ điều khiển đánh giá", C),
      ("Mô hình phân loại cảm xúc", S), DB], [
         (0, 1, "c", "Chọn số sao, nhập nội dung, đính kèm ảnh/video"),
         (1, 2, "c", "Gửi đánh giá"),
         (2, 4, "c", "Lấy sản phẩm đã mua của người dùng"),
         (4, 2, "r", "Dòng sản phẩm, trạng thái đơn"),
         (2, 2, "s", "Kiểm tra đơn đã giao"),
         (2, 4, "c", "Kiểm tra sản phẩm chưa được đánh giá"),
         (4, 2, "r", "Kết quả kiểm tra"),
         (2, 2, "s", "Kiểm tra số sao (1–5) và nội dung"),
         (2, 3, "c", "Gửi nội dung bình luận"),
         (3, 3, "s", "Làm sạch, tách từ, TF-IDF, Logistic Regression"),
         (3, 2, "r", "Nhãn cảm xúc + độ tin cậy"),
         (2, 4, "c", "Lưu đánh giá kèm nhãn cảm xúc"),
         (2, 4, "c", "Lưu ảnh/video đính kèm (tối đa 5)"),
         (2, 1, "r", "Quay về mục đánh giá, báo cảm ơn"),
         (1, 0, "r", "Hiển thị đánh giá kèm nhãn cảm xúc"),
     ]),
    ("Hình 3.14 - Yêu thích sản phẩm",
     [KH, ("Giao diện sản phẩm", B), ("Bộ điều khiển yêu thích", C), DB], [
         (0, 1, "c", "Bấm biểu tượng trái tim"),
         (1, 2, "c", "Gửi yêu cầu thêm/bỏ yêu thích"),
         (2, 3, "c", "Lấy sản phẩm và danh sách yêu thích"),
         (3, 2, "r", "Sản phẩm, danh sách yêu thích"),
         (2, 2, "s", "Kiểm tra sản phẩm đã có trong danh sách chưa"),
         (2, 3, "c", "Thêm vào hoặc bỏ khỏi danh sách yêu thích"),
         (2, 1, "r", "Quay lại trang đang xem, báo đã thêm/đã bỏ"),
         (1, 0, "r", "Hiển thị trái tim đã cập nhật"),
         (0, 1, "c", "Mở trang Sản phẩm yêu thích"),
         (1, 2, "c", "Yêu cầu danh sách yêu thích"),
         (2, 3, "c", "Lấy sản phẩm yêu thích đang bán"),
         (3, 2, "r", "Danh sách sản phẩm yêu thích"),
         (2, 1, "r", "Trả trang Sản phẩm yêu thích"),
         (1, 0, "r", "Hiển thị sản phẩm yêu thích"),
     ]),
    ("Hình 3.15 - Cập nhật hồ sơ cá nhân",
     [KH, ("Giao diện hồ sơ", B), ("Bộ điều khiển tài khoản", C), DB], [
         (0, 1, "c", "Mở trang hồ sơ"),
         (1, 2, "c", "Yêu cầu thông tin hồ sơ"),
         (2, 3, "c", "Lấy thông tin người dùng"),
         (3, 2, "r", "Thông tin người dùng"),
         (2, 1, "r", "Trả form hồ sơ đã điền sẵn"),
         (1, 0, "r", "Hiển thị form hồ sơ"),
         (0, 1, "c", "Sửa họ tên, email, SĐT, địa chỉ, ảnh đại diện"),
         (1, 2, "c", "Gửi thông tin cập nhật"),
         (2, 2, "s", "Kiểm tra dữ liệu (email bắt buộc)"),
         (2, 3, "c", "Lưu thông tin và ảnh đại diện"),
         (2, 1, "r", "Tải lại trang hồ sơ, báo cập nhật thành công"),
         (1, 0, "r", "Hiển thị hồ sơ mới"),
     ]),
    ("Hình 3.16 - Quản lí bình luận và thống kê cảm xúc (Quản trị viên)",
     [("Quản trị viên", A), ("Giao diện trang quản trị", B), ("Bộ điều khiển quản trị", C), DB], [
         (0, 1, "c", "Mở mục Đánh giá, chọn bộ lọc (sản phẩm, số sao, cảm xúc)"),
         (1, 2, "c", "Yêu cầu danh sách đánh giá theo bộ lọc"),
         (2, 3, "c", "Lấy đánh giá theo bộ lọc"),
         (3, 2, "r", "Danh sách đánh giá, nhãn cảm xúc, độ tin cậy"),
         (2, 3, "c", "Đếm số đánh giá Tích cực / Trung lập / Tiêu cực"),
         (3, 2, "r", "Số liệu tổng và theo từng sản phẩm"),
         (2, 2, "s", "Tính tỉ lệ % cảm xúc"),
         (2, 1, "r", "Trả danh sách kèm thống kê, biểu đồ"),
         (1, 0, "r", "Hiển thị danh sách và biểu đồ cảm xúc"),
         (0, 1, "c", "Chọn đánh giá vi phạm, bấm Xoá, xác nhận"),
         (1, 2, "c", "Gửi yêu cầu xoá đánh giá"),
         (2, 3, "c", "Xoá đánh giá và tệp đính kèm"),
         (2, 1, "r", "Báo xoá thành công, tải lại danh sách"),
         (1, 0, "r", "Hiển thị danh sách đã cập nhật"),
     ]),
]


def wrap(text, limit=34):
    """Chia nhãn dài thành 2 dòng tại khoảng trắng gần giữa nhất."""
    if len(text) <= limit:
        return text
    mid = len(text) // 2
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    cut = min(spaces, key=lambda i: abs(i - mid))
    return text[:cut] + "<br>" + text[cut + 1:]


def layout(name, cols, steps):
    y, items = 140, []
    for n, (a, b, kind, label) in enumerate(steps, 1):
        text = f"{n}. {label}"
        if kind != "s":
            text = wrap(text)
            if "<br>" in text and n > 1:
                y += 15  # chừa chỗ cho nhãn 2 dòng phía trên mũi tên
        else:
            text = wrap(text, 30)
        items.append(("m", y, a, b, kind, text))
        y += 60 if kind == "s" else 45
    return {"name": name, "cols": cols, "height": y + 10 - base.TOP, "items": items}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base.DIAGRAMS = [layout(*spec) for spec in SPECS]
    base.OUT = OUT
    base.write_drawio()
    if "--preview" in sys.argv:
        base.preview(sys.argv[sys.argv.index("--preview") + 1])


if __name__ == "__main__":
    main()
