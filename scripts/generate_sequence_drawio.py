"""
Sinh file draw.io chứa các sơ đồ tuần tự (Hình 3.3 -> 3.11) của đồ án Astraea,
bám đúng luồng xử lý thực tế trong code (accounts, cart, orders, reviews, tryon).

Chạy:  .venv\\Scripts\\python.exe scripts\\generate_sequence_drawio.py
Kết quả: bug_promtp/sodotuantu.drawio.xml (+ ảnh xem trước PNG nếu truyền --preview <thư mục>)
"""

import html
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "bug_promtp" / "sodotuantu.drawio.xml"

COL_X = [100, 320, 540, 760, 980]  # tâm từng cột
COL_W = 150
HEAD_H = 60
TOP = 40
FONT = "fontFamily=Times New Roman;"

LIFELINE = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;"
            "dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;strokeColor=#000000;"
            "fillColor=#FFFFFF;fontColor=#000000;strokeWidth=1.2;size=%d;%sfontSize=13;" % (HEAD_H, FONT))
CALL = ("html=1;verticalAlign=bottom;labelBackgroundColor=#FFFFFF;endArrow=block;endFill=1;rounded=0;strokeColor=#000000;"
        "fontColor=#000000;%sfontSize=12;" % FONT)
RETURN = ("html=1;verticalAlign=bottom;labelBackgroundColor=#FFFFFF;endArrow=open;endFill=0;endSize=8;dashed=1;rounded=0;"
          "strokeColor=#000000;fontColor=#000000;%sfontSize=12;" % FONT)
SELF = ("html=1;align=left;verticalAlign=middle;spacingLeft=6;endArrow=block;endFill=1;rounded=0;"
        "strokeColor=#000000;fontColor=#000000;labelBackgroundColor=#FFFFFF;%sfontSize=12;" % FONT)
FRAME = ("shape=umlFrame;whiteSpace=wrap;html=1;pointerEvents=0;strokeColor=#000000;fillColor=none;"
         "fontColor=#000000;width=45;height=20;fontStyle=1;%sfontSize=12;" % FONT)
GUARD = ("text;html=1;align=left;verticalAlign=middle;fontStyle=2;fontColor=#000000;"
         "%sfontSize=12;" % FONT)
DIVIDER = "endArrow=none;dashed=1;html=1;strokeColor=#000000;"
NOTE = ("shape=note;whiteSpace=wrap;html=1;size=14;fillColor=#FFFFFF;strokeColor=#000000;"
        "fontColor=#000000;align=left;verticalAlign=middle;spacingLeft=6;spacingRight=4;"
        "%sfontSize=12;" % FONT)

# Kiểu cột: (tên, khuôn mẫu)
ACTOR, BOUNDARY, CONTROL, ENTITY, SERVICE = "Actor", "Boundary", "Control", "Entity", "Service"

# Mỗi sơ đồ: cols, height (chiều cao lifeline), items
#   ("m", y, from, to, kind, label)  kind: c=gọi, r=trả về, s=tự gọi
#   ("alt", x, y, w, h, guard1, divider_y, guard2)
#   ("loop"/"opt", x, y, w, h, guard)
#   ("note", x, y, w, h, text)
DIAGRAMS = [
    {
        "name": "Hình 3.3 - Đăng nhập",
        "cols": [("Khách hàng", ACTOR), ("Giao diện đăng nhập", BOUNDARY),
                 ("Bộ điều khiển đăng nhập", CONTROL), ("Cơ sở dữ liệu", ENTITY)],
        "height": 760,
        "items": [
            ("alt", 230, 390, 640, 320, "[Sai thông tin]", 470, "[Đúng thông tin]"),
            ("opt", 450, 545, 410, 80, "[Có giỏ hàng khách vãng lai]"),
            ("m", 140, 0, 1, "c", "1: Nhập tên đăng nhập, mật khẩu"),
            ("m", 190, 1, 2, "c", "2: Gửi yêu cầu đăng nhập"),
            ("m", 240, 2, 3, "c", "3: Tìm tài khoản theo tên đăng nhập"),
            ("m", 290, 3, 2, "r", "4: Thông tin tài khoản"),
            ("m", 330, 2, 2, "s", "5: Kiểm tra mật khẩu,<br>tài khoản còn hoạt động"),
            ("m", 440, 2, 1, "r", "6: Báo lỗi sai tên đăng nhập<br>hoặc mật khẩu"),
            ("m", 520, 2, 3, "c", "7: Tạo phiên đăng nhập"),
            ("m", 600, 2, 3, "c", "8: Gộp giỏ hàng khách vào tài khoản"),
            ("m", 670, 2, 1, "r", "9: Chuyển về trang chủ<br>(quản trị viên → trang quản trị)"),
            ("m", 750, 1, 0, "r", "10: Hiển thị kết quả"),
        ],
    },
    {
        "name": "Hình 3.4 - Đăng ký",
        "cols": [("Khách hàng", ACTOR), ("Giao diện đăng ký", BOUNDARY),
                 ("Bộ điều khiển đăng ký", CONTROL), ("Cơ sở dữ liệu", ENTITY)],
        "height": 810,
        "items": [
            ("alt", 230, 390, 640, 370, "[Không hợp lệ]", 470, "[Hợp lệ]"),
            ("m", 140, 0, 1, "c", "1: Nhập tên đăng nhập, email,<br>SĐT, địa chỉ, mật khẩu"),
            ("m", 190, 1, 2, "c", "2: Gửi yêu cầu đăng ký"),
            ("m", 240, 2, 3, "c", "3: Kiểm tra tên đăng nhập đã tồn tại"),
            ("m", 290, 3, 2, "r", "4: Kết quả kiểm tra"),
            ("m", 330, 2, 2, "s", "5: Kiểm tra email bắt buộc,<br>độ mạnh và khớp mật khẩu"),
            ("m", 440, 2, 1, "r", "6: Báo lỗi từng trường"),
            ("m", 520, 2, 3, "c", "7: Lưu tài khoản mới<br>(mật khẩu đã mã hoá)"),
            ("m", 580, 2, 3, "c", "8: Tự tạo Ví, Giỏ hàng,<br>Danh sách yêu thích"),
            ("m", 640, 2, 3, "c", "9: Gộp giỏ hàng khách vãng lai"),
            ("m", 700, 2, 1, "r", "10: Tự đăng nhập,<br>chuyển về trang chủ"),
            ("m", 800, 1, 0, "r", "11: Hiển thị lời chào mừng"),
        ],
    },
    {
        "name": "Hình 3.5 - Tìm kiếm sản phẩm",
        "cols": [("Khách hàng", ACTOR), ("Giao diện tìm kiếm", BOUNDARY),
                 ("Bộ điều khiển sản phẩm", CONTROL), ("Cơ sở dữ liệu", ENTITY)],
        "height": 530,
        "items": [
            ("alt", 230, 320, 420, 160, "[Có kết quả]", 400, "[Không có kết quả]"),
            ("m", 140, 0, 1, "c", "1: Nhập từ khoá, bấm Tìm"),
            ("m", 190, 1, 2, "c", "2: Gửi từ khoá tìm kiếm"),
            ("m", 240, 2, 3, "c", "3: Tìm sản phẩm đang bán<br>theo tên, mô tả, danh mục"),
            ("m", 290, 3, 2, "r", "4: Danh sách sản phẩm"),
            ("m", 370, 2, 1, "r", "5: Danh sách sản phẩm tìm được"),
            ("m", 450, 2, 1, "r", "6: Thông báo không tìm thấy"),
            ("m", 520, 1, 0, "r", "7: Hiển thị kết quả"),
        ],
    },
    {
        "name": "Hình 3.6 - Thêm vào giỏ hàng",
        "cols": [("Khách hàng", ACTOR), ("Giao diện chi tiết sản phẩm", BOUNDARY),
                 ("Bộ điều khiển giỏ hàng", CONTROL), ("Cơ sở dữ liệu", ENTITY)],
        "height": 690,
        "items": [
            ("alt", 230, 320, 640, 320, "[Hết hàng]", 400, "[Còn hàng]"),
            ("m", 140, 0, 1, "c", "1: Chọn số lượng,<br>bấm Thêm vào giỏ"),
            ("m", 190, 1, 2, "c", "2: Gửi yêu cầu thêm vào giỏ"),
            ("m", 240, 2, 3, "c", "3: Lấy thông tin sản phẩm, tồn kho"),
            ("m", 290, 3, 2, "r", "4: Thông tin sản phẩm"),
            ("m", 370, 2, 1, "r", "5: Báo sản phẩm đã hết hàng"),
            ("m", 450, 2, 3, "c", "6: Lấy giỏ hàng (theo tài khoản<br>hoặc phiên khách)"),
            ("m", 500, 3, 2, "r", "7: Giỏ hàng"),
            ("m", 560, 2, 3, "c", "8: Thêm hoặc cộng dồn số lượng<br>(không vượt tồn kho)"),
            ("m", 610, 2, 1, "r", "9: Chuyển tới giỏ hàng,<br>báo thêm thành công"),
            ("m", 680, 1, 0, "r", "10: Hiển thị giỏ hàng"),
        ],
    },
    {
        "name": "Hình 3.7 - Đặt hàng và thanh toán",
        "cols": [("Khách hàng", ACTOR), ("Giao diện giỏ hàng", BOUNDARY),
                 ("Bộ điều khiển đơn hàng", CONTROL), ("Cơ sở dữ liệu", ENTITY)],
        "height": 830,
        "items": [
            ("alt", 230, 400, 640, 380, "[Không hợp lệ]", 480, "[Hợp lệ]"),
            ("loop", 450, 555, 410, 90, "[Mỗi sản phẩm trong giỏ]"),
            ("note", 890, 500, 210, 120,
             "Bước 7–9 chạy trong một giao dịch (transaction): lỗi giữa chừng thì huỷ toàn bộ."
             "<br>Thanh toán là giả lập, không gọi cổng thanh toán thật."),
            ("m", 140, 0, 1, "c", "1: Chọn thanh toán, vận chuyển,<br>nhập người nhận"),
            ("m", 190, 1, 2, "c", "2: Gửi yêu cầu đặt hàng"),
            ("m", 240, 2, 3, "c", "3: Lấy giỏ hàng và các sản phẩm"),
            ("m", 290, 3, 2, "r", "4: Danh sách sản phẩm trong giỏ"),
            ("m", 330, 2, 2, "s", "5: Kiểm tra giỏ trống, tồn kho,<br>thanh toán, vận chuyển, người nhận"),
            ("m", 450, 2, 1, "r", "6: Báo lỗi, giữ nguyên giỏ hàng"),
            ("m", 530, 2, 3, "c", "7: Tạo đơn hàng"),
            ("m", 620, 2, 3, "c", "8: Lưu chi tiết đơn (giá lúc mua),<br>trừ tồn kho"),
            ("m", 690, 2, 3, "c", "9: Xoá giỏ hàng"),
            ("m", 750, 2, 1, "r", "10: Chuyển tới Đơn hàng của tôi,<br>báo thành công"),
            ("m", 820, 1, 0, "r", "11: Hiển thị đơn vừa đặt"),
        ],
    },
    {
        "name": "Hình 3.8 - Đánh giá và phân loại cảm xúc",
        "cols": [("Khách hàng", ACTOR), ("Giao diện chi tiết sản phẩm", BOUNDARY),
                 ("Bộ điều khiển đánh giá", CONTROL), ("Mô hình phân loại cảm xúc", SERVICE),
                 ("Cơ sở dữ liệu", ENTITY)],
        "height": 850,
        "items": [
            ("alt", 230, 320, 860, 480,
             "[Đơn chưa giao / đã đánh giá / thiếu số sao hoặc nội dung]", 400, "[Đủ điều kiện]"),
            ("opt", 450, 635, 630, 85, "[Có ảnh/video đính kèm]"),
            ("note", 1110, 430, 200, 90,
             "Nhãn: Tích cực / Trung lập / Tiêu cực.<br>Mô hình huấn luyện sẵn: sentiment_model.joblib"),
            ("m", 140, 0, 1, "c", "1: Chọn số sao, nhập nội dung,<br>đính kèm ảnh/video"),
            ("m", 190, 1, 2, "c", "2: Gửi đánh giá"),
            ("m", 240, 2, 4, "c", "3: Kiểm tra đơn đã giao,<br>sản phẩm chưa được đánh giá"),
            ("m", 290, 4, 2, "r", "4: Kết quả kiểm tra"),
            ("m", 370, 2, 1, "r", "5: Báo lỗi"),
            ("m", 450, 2, 3, "c", "6: Gửi nội dung bình luận"),
            ("m", 490, 3, 3, "s", "7: Làm sạch, tách từ,<br>TF-IDF, Logistic Regression"),
            ("m", 560, 3, 2, "r", "8: Nhãn cảm xúc + độ tin cậy"),
            ("m", 610, 2, 4, "c", "9: Lưu đánh giá kèm nhãn cảm xúc"),
            ("m", 700, 2, 4, "c", "10: Lưu tệp đính kèm (tối đa 5)"),
            ("m", 770, 2, 1, "r", "11: Hiển thị đánh giá<br>kèm nhãn cảm xúc"),
            ("m", 840, 1, 0, "r", "12: Xem đánh giá vừa gửi"),
        ],
    },
    {
        "name": "Hình 3.9 - Thử kính ảo",
        "cols": [("Khách hàng", ACTOR), ("Cửa sổ thử kính", BOUNDARY),
                 ("Máy chủ xử lý (WebSocket)", CONTROL),
                 ("Mô-đun xử lý ảnh (MediaPipe, OpenCV)", SERVICE), ("Cơ sở dữ liệu", ENTITY)],
        "height": 960,
        "items": [
            ("alt", 20, 240, 1080, 740, "[Từ chối camera]", 330, "[Cho phép]"),
            ("loop", 40, 560, 1040, 290, "[Mỗi khung hình, khoảng 40 ms/lần]"),
            ("note", 1120, 640, 210, 120,
             "Mất khuôn mặt từ 3 khung liên tiếp: máy chủ trả ảnh gốc với cờ = 0, "
             "cửa sổ hiện “Không phát hiện khuôn mặt”."),
            ("m", 140, 0, 1, "c", "1: Bấm Thử kính"),
            ("m", 180, 1, 1, "s", "2: Xin quyền mở webcam"),
            ("m", 300, 1, 0, "r", "3: Báo không mở được camera"),
            ("m", 380, 1, 2, "c", "4: Mở kết nối WebSocket"),
            ("m", 430, 1, 2, "c", "5: Gửi mẫu kính đã chọn"),
            ("m", 480, 2, 4, "c", "6: Lấy thông tin mẫu kính<br>(đường dẫn ảnh PNG)"),
            ("m", 530, 4, 2, "r", "7: Thông tin mẫu kính"),
            ("m", 620, 1, 2, "c", "8: Gửi khung hình webcam (JPEG)"),
            ("m", 670, 2, 3, "c", "9: Nhận diện mắt, làm mượt,<br>dán kính"),
            ("m", 720, 3, 2, "r", "10: Khung hình đã ghép kính"),
            ("m", 780, 2, 1, "r", "11: Khung hình + cờ<br>có/không có khuôn mặt"),
            ("m", 830, 1, 0, "r", "12: Hiển thị hình đeo kính"),
            ("m", 900, 0, 1, "c", "13: Đóng cửa sổ"),
            ("m", 950, 1, 2, "c", "14: Ngắt kết nối, tắt camera"),
        ],
    },
    {
        "name": "Hình 3.10 - Huỷ đơn hàng (tuỳ chọn)",
        "cols": [("Khách hàng", ACTOR), ("Giao diện đơn hàng của tôi", BOUNDARY),
                 ("Bộ điều khiển đơn hàng", CONTROL), ("Cơ sở dữ liệu", ENTITY)],
        "height": 690,
        "items": [
            ("alt", 230, 320, 640, 320, "[Đơn đã huỷ từ trước]", 400, "[Đơn chưa huỷ]"),
            ("loop", 450, 475, 410, 85, "[Mỗi sản phẩm trong đơn]"),
            ("note", 890, 450, 190, 60, "Bước 6–7 chạy trong một giao dịch (transaction)."),
            ("m", 140, 0, 1, "c", "1: Bấm Huỷ đơn"),
            ("m", 190, 1, 2, "c", "2: Gửi yêu cầu huỷ đơn"),
            ("m", 240, 2, 3, "c", "3: Lấy đơn hàng của người dùng"),
            ("m", 290, 3, 2, "r", "4: Thông tin đơn hàng"),
            ("m", 370, 2, 1, "r", "5: Báo đơn đã được huỷ từ trước"),
            ("m", 450, 2, 3, "c", "6: Đổi trạng thái đơn thành Đã huỷ"),
            ("m", 540, 2, 3, "c", "7: Cộng lại tồn kho sản phẩm"),
            ("m", 610, 2, 1, "r", "8: Báo huỷ đơn thành công"),
            ("m", 680, 1, 0, "r", "9: Hiển thị danh sách đơn<br>đã cập nhật"),
        ],
    },
    {
        "name": "Hình 3.11 - Cập nhật trạng thái giao hàng (tuỳ chọn)",
        "cols": [("Quản trị viên", ACTOR), ("Giao diện trang quản trị", BOUNDARY),
                 ("Bộ điều khiển quản trị", CONTROL), ("Cơ sở dữ liệu", ENTITY)],
        "height": 600,
        "items": [
            ("note", 890, 380, 200, 80,
             "Các trường khác của đơn chỉ đọc; không cho tạo đơn mới từ trang quản trị."),
            ("m", 140, 0, 1, "c", "1: Mở mục Đơn hàng"),
            ("m", 190, 1, 2, "c", "2: Yêu cầu danh sách đơn hàng"),
            ("m", 240, 2, 3, "c", "3: Lấy danh sách đơn hàng"),
            ("m", 290, 3, 2, "r", "4: Danh sách đơn hàng"),
            ("m", 340, 2, 1, "r", "5: Hiển thị danh sách"),
            ("m", 390, 0, 1, "c", "6: Chọn đơn, đổi trạng thái<br>giao hàng, bấm Lưu"),
            ("m", 440, 1, 2, "c", "7: Gửi trạng thái giao hàng mới"),
            ("m", 490, 2, 3, "c", "8: Cập nhật trạng thái giao hàng"),
            ("m", 540, 2, 1, "r", "9: Báo lưu thành công"),
            ("m", 590, 1, 0, "r", "10: Hiển thị thông báo"),
        ],
    },
]


def esc(s):
    return html.escape(s, quote=True)


def vertex(cid, value, style, x, y, w, h):
    return (f'<mxCell id="{cid}" value="{esc(value)}" style="{esc(style)}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def edge(cid, value, style, p1, p2, points=()):
    pts = ""
    if points:
        pts = '<Array as="points">' + "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points) + "</Array>"
    return (f'<mxCell id="{cid}" value="{esc(value)}" style="{esc(style)}" edge="1" parent="1">'
            f'<mxGeometry relative="1" as="geometry">'
            f'<mxPoint x="{p1[0]}" y="{p1[1]}" as="sourcePoint"/>'
            f'<mxPoint x="{p2[0]}" y="{p2[1]}" as="targetPoint"/>{pts}</mxGeometry></mxCell>')


def build_page(idx, d):
    cells = []
    n = 0

    def nid():
        nonlocal n
        n += 1
        return f"p{idx}_{n}"

    # khung và ghi chú vẽ trước để nằm dưới mũi tên
    for it in d["items"]:
        if it[0] == "alt":
            _, x, y, w, h, g1, dy, g2 = it
            cells.append(vertex(nid(), "alt", FRAME, x, y, w, h))
            cells.append(vertex(nid(), g1, GUARD, x + 50, y, 420, 20))
            cells.append(edge(nid(), "", DIVIDER, (x, dy), (x + w, dy)))
            cells.append(vertex(nid(), g2, GUARD, x + 8, dy + 2, 300, 20))
        elif it[0] in ("loop", "opt"):
            _, x, y, w, h, g = it
            cells.append(vertex(nid(), it[0], FRAME, x, y, w, h))
            cells.append(vertex(nid(), g, GUARD, x + 50, y, 320, 20))
        elif it[0] == "note":
            _, x, y, w, h, t = it
            cells.append(vertex(nid(), t, NOTE, x, y, w, h))

    for i, (name, stereo) in enumerate(d["cols"]):
        cx = COL_X[i]
        cells.append(vertex(nid(), f"<b>{name}</b><br>«{stereo}»", LIFELINE,
                            cx - COL_W // 2, TOP, COL_W, d["height"]))

    for it in d["items"]:
        if it[0] != "m":
            continue
        _, y, a, b, kind, label = it
        xa, xb = COL_X[a], COL_X[b]
        if kind == "s":
            cells.append(edge(nid(), label, SELF, (xa, y), (xa, y + 30),
                              [(xa + 40, y), (xa + 40, y + 30)]))
        else:
            cells.append(edge(nid(), label, CALL if kind == "c" else RETURN, (xa, y), (xb, y)))

    return (f'<diagram id="seq_{idx}" name="{esc(d["name"])}">'
            f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
            f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1360" '
            f'pageHeight="1080" background="#FFFFFF" math="0" shadow="0"><root>'
            f'<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + "</root></mxGraphModel></diagram>")


def write_drawio():
    pages = "".join(build_page(i + 1, d) for i, d in enumerate(DIAGRAMS))
    xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<mxfile host="app.diagrams.net" '
           f'pages="{len(DIAGRAMS)}">{pages}</mxfile>\n')
    OUT.write_text(xml, encoding="utf-8")
    print("Đã ghi", OUT)


def preview(out_dir):
    """Vẽ nháp bằng Pillow để kiểm tra chồng chéo (không thay thế draw.io)."""
    from PIL import Image, ImageDraw, ImageFont

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    f = ImageFont.truetype("C:/Windows/Fonts/times.ttf", 12)
    fb = ImageFont.truetype("C:/Windows/Fonts/timesbd.ttf", 12)
    fi = ImageFont.truetype("C:/Windows/Fonts/timesi.ttf", 12)

    def lines(t):
        return re.sub(r"<[^>]+>", "", t.replace("<br>", "\n")).split("\n")

    def dashed(dr, p1, p2, dash=6):
        (x1, y1), (x2, y2) = p1, p2
        length = max(abs(x2 - x1), abs(y2 - y1))
        for s in range(0, int(length), dash * 2):
            e = min(s + dash, length)
            fx = lambda t: x1 + (x2 - x1) * t / length
            fy = lambda t: y1 + (y2 - y1) * t / length
            dr.line([(fx(s), fy(s)), (fx(e), fy(e))], fill="black")

    for idx, d in enumerate(DIAGRAMS, 1):
        img = Image.new("RGB", (1360, TOP + d["height"] + 60), "white")
        dr = ImageDraw.Draw(img)
        for it in d["items"]:
            if it[0] == "alt":
                _, x, y, w, h, g1, dy, g2 = it
                dr.rectangle([x, y, x + w, y + h], outline="black")
                dr.rectangle([x, y, x + 45, y + 20], outline="black")
                dr.text((x + 8, y + 3), "alt", font=fb, fill="black")
                dr.text((x + 50, y + 3), g1, font=fi, fill="black")
                dashed(dr, (x, dy), (x + w, dy))
                dr.text((x + 8, dy + 4), g2, font=fi, fill="black")
            elif it[0] in ("loop", "opt"):
                _, x, y, w, h, g = it
                dr.rectangle([x, y, x + w, y + h], outline="black")
                dr.rectangle([x, y, x + 45, y + 20], outline="black")
                dr.text((x + 8, y + 3), it[0], font=fb, fill="black")
                dr.text((x + 50, y + 3), g, font=fi, fill="black")
            elif it[0] == "note":
                _, x, y, w, h, t = it
                dr.rectangle([x, y, x + w, y + h], outline="black", fill="white")
                dr.multiline_text((x + 6, y + 6), "\n".join(lines(t)), font=f, fill="black")
        for i, (name, stereo) in enumerate(d["cols"]):
            cx = COL_X[i]
            dr.rectangle([cx - COL_W // 2, TOP, cx + COL_W // 2, TOP + HEAD_H], outline="black", fill="white")
            dr.multiline_text((cx, TOP + HEAD_H // 2), f"{name}\n«{stereo}»", font=fb, fill="black",
                              anchor="mm", align="center")
            dashed(dr, (cx, TOP + HEAD_H), (cx, TOP + d["height"]))
        for it in d["items"]:
            if it[0] != "m":
                continue
            _, y, a, b, kind, label = it
            xa, xb = COL_X[a], COL_X[b]
            txt = "\n".join(lines(label))
            if kind == "s":
                dr.line([(xa, y), (xa + 40, y), (xa + 40, y + 30), (xa + 4, y + 30)], fill="black")
                dr.polygon([(xa, y + 30), (xa + 8, y + 26), (xa + 8, y + 34)], fill="black")
                bb = dr.multiline_textbbox((xa + 46, y + 15), txt, font=f, anchor="lm")
                dr.rectangle(bb, fill="white")
                dr.multiline_text((xa + 46, y + 15), txt, font=f, fill="black", anchor="lm")
                continue
            if kind == "c":
                dr.line([(xa, y), (xb, y)], fill="black")
            else:
                dashed(dr, (xa, y), (xb, y))
            s = 1 if xb > xa else -1
            if kind == "c":
                dr.polygon([(xb, y), (xb - 9 * s, y - 4), (xb - 9 * s, y + 4)], fill="black")
            else:
                dr.line([(xb - 9 * s, y - 4), (xb, y), (xb - 9 * s, y + 4)], fill="black")
            dr.multiline_text(((xa + xb) / 2, y - 3), txt, font=f, fill="black", anchor="md", align="center")
        img.save(out_dir / f"preview_{idx}.png")
    print("Đã vẽ nháp vào", out_dir)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    write_drawio()
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
