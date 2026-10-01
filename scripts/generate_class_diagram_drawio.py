"""
Sinh file Astraea_ClassDiagram.drawio (UML Class Diagram) từ đúng các model
Django của 8 app: accounts, products, cart, orders, favorites, reviews,
tryon, wallet. Thuộc tính, kiểu, ràng buộc và phương thức lấy theo models.py
(đã đối chiếu bằng Django _meta), không thêm trường không có thật.

Chạy:  python scripts/generate_class_diagram_drawio.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

ROW = 20          # chiều cao 1 dòng thuộc tính/phương thức
HEAD = 40         # chiều cao phần tên lớp
W = 340           # chiều rộng mặc định của một lớp

cells = []        # các mxCell dạng chuỗi XML
_id = [0]


def nid(prefix):
    _id[0] += 1
    return f"{prefix}{_id[0]}"


def cls(key, name, x, y, attrs, methods=(), stereotype=None, width=W,
        fill="#dae8fc", stroke="#6c8ebf"):
    """Một lớp UML = swimlane (tên) + các dòng thuộc tính + vạch ngăn + phương thức."""
    title = name if not stereotype else f"«{stereotype}»\n{name}"
    head = HEAD if not stereotype else HEAD + 14
    n_rows = len(attrs) + len(methods)
    h = head + n_rows * ROW + (8 if methods else 0) + 6
    style = ("swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;"
             "horizontal=1;startSize={s};horizontalStack=0;resizeParent=1;resizeParentMax=0;"
             "resizeLast=0;collapsible=0;marginBottom=0;whiteSpace=wrap;html=0;"
             "fillColor={f};strokeColor={st};fontSize=14;swimlaneFillColor=#ffffff;").format(
                 s=head, f=fill, st=stroke)
    cells.append(f'<mxCell id="{key}" value="{escape(title).replace(chr(10), "&#xa;")}" style="{style}" '
                 f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{width}" height="{h}" as="geometry"/></mxCell>')
    cy = head
    row_style = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=6;"
                 "spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
                 "whiteSpace=wrap;html=0;fontSize=12;fontFamily=Consolas;")
    for a in attrs:
        cells.append(f'<mxCell id="{nid(key + "_a")}" value="{escape(a)}" style="{row_style}" vertex="1" '
                     f'parent="{key}"><mxGeometry y="{cy}" width="{width}" height="{ROW}" as="geometry"/></mxCell>')
        cy += ROW
    if methods:
        cells.append(f'<mxCell id="{nid(key + "_l")}" value="" style="line;strokeWidth=1;fillColor=none;align=left;'
                     f'verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;'
                     f'points=[];portConstraint=eastwest;strokeColor=inherit;" vertex="1" parent="{key}">'
                     f'<mxGeometry y="{cy}" width="{width}" height="8" as="geometry"/></mxCell>')
        cy += 8
        for m in methods:
            cells.append(f'<mxCell id="{nid(key + "_m")}" value="{escape(m)}" style="{row_style}" vertex="1" '
                         f'parent="{key}"><mxGeometry y="{cy}" width="{width}" height="{ROW}" as="geometry"/></mxCell>')
            cy += ROW
    return h


def edge(src, dst, kind, src_mult="", dst_mult="", label="", exit=None, entry=None, points=()):
    """kind: assoc | comp (src là toàn thể ◆) | inherit (src kế thừa dst)."""
    base = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;fontSize=12;endSize=12;startSize=14;"
    if kind == "comp":
        base += "startArrow=diamondThin;startFill=1;endArrow=none;"
    elif kind == "inherit":
        base += "endArrow=block;endFill=0;"
    else:
        base += "endArrow=none;"
    if exit:
        base += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
    if entry:
        base += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
    eid = nid("e")
    pts = ""
    if points:
        pts = '<Array as="points">' + "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in points) + "</Array>"
    cells.append(f'<mxCell id="{eid}" value="{escape(label)}" style="{base}labelBackgroundColor=#ffffff;" edge="1" '
                 f'parent="1" source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry">{pts}</mxGeometry></mxCell>')
    lab = "resizable=0;html=0;align={a};verticalAlign=bottom;labelBackgroundColor=#ffffff;fontSize=12;fontStyle=1;"
    if src_mult:
        cells.append(f'<mxCell id="{nid("m")}" value="{src_mult}" style="{lab.format(a="left")}" connectable="0" vertex="1" '
                     f'parent="{eid}"><mxGeometry x="-0.85" relative="1" as="geometry"><mxPoint x="4" y="-2" as="offset"/></mxGeometry></mxCell>')
    if dst_mult:
        cells.append(f'<mxCell id="{nid("m")}" value="{dst_mult}" style="{lab.format(a="right")}" connectable="0" vertex="1" '
                     f'parent="{eid}"><mxGeometry x="0.85" relative="1" as="geometry"><mxPoint x="-4" y="-2" as="offset"/></mxGeometry></mxCell>')


def note(x, y, w, h, text):
    cells.append(f'<mxCell id="{nid("n")}" value="{escape(text).replace(chr(10), "&#xa;")}" style="shape=note;whiteSpace=wrap;html=0;size=14;'
                 f'align=left;spacingLeft=8;verticalAlign=top;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=12;" '
                 f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


# ---------------------------------------------------------------- lớp
DJ = dict(fill="#f5f5f5", stroke="#666666")          # lớp có sẵn của Django
EN = dict(fill="#e1d5e7", stroke="#9673a6", width=230)  # enumeration (TextChoices)

X0, X1, X2, X3, X4, X5 = 40, 480, 920, 1360, 1800, 2240

cls("AbstractUser", "AbstractUser", X0, 40, [
    "+ id: BigInt {PK}",
    "+ username: str[150] {unique}",
    "+ password: str[128]  (hash)",
    "+ email: str[254]",
    "+ first_name: str[150]",
    "+ last_name: str[150]",
    "+ is_staff: bool",
    "+ is_active: bool",
    "+ is_superuser: bool",
    "+ last_login: datetime [0..1]",
    "+ date_joined: datetime",
], ["+ set_password(raw): void", "+ check_password(raw): bool"], stereotype="Django", **DJ)

cls("User", "User", X0, 470, [
    "+ phone_number: str[15]",
    "+ address: str[255]",
    "+ avatar: Image [0..1]",
    "+ created_at: datetime",
], stereotype="accounts")

cls("Wallet", "Wallet", X0, 1040, [
    "+ id: BigInt {PK}",
    "+ user: User {FK, unique}",
    "+ balance: Decimal(14,2) = 0",
    "+ created_at: datetime",
    "+ updated_at: datetime",
], ["+ deposit(amount, description): Decimal",
    "+ withdraw(amount, description): Decimal"], stereotype="wallet")

cls("Transaction", "Transaction", X0, 1330, [
    "+ id: BigInt {PK}",
    "+ wallet: Wallet {FK}",
    "+ transaction_type: TransactionType",
    "+ amount: Decimal(14,2)",
    "+ balance_after: Decimal(14,2)",
    "+ description: str[255]",
    "+ created_at: datetime",
], stereotype="wallet")

cls("Cart", "Cart", X1, 40, [
    "+ id: BigInt {PK}",
    "+ user: User {FK, unique} [0..1]",
    "+ session_key: str[40] {unique} [0..1]",
    "+ created_at: datetime",
], ["+ merge_from(other_cart): void",
    "+ add_product(product, quantity=1): CartItem",
    "+ /total_items: int",
    "+ /total_price: Decimal"], stereotype="cart")

cls("CartItem", "CartItem", X2, 40, [
    "+ id: BigInt {PK}",
    "+ cart: Cart {FK}",
    "+ product: Product {FK}",
    "+ quantity: int = 1",
    "+ added_at: datetime",
    "{unique (cart, product)}",
], ["+ /line_total: Decimal"], stereotype="cart")

cls("Favorite", "Favorite", X1, 420, [
    "+ id: BigInt {PK}",
    "+ user: User {FK, unique}",
    "+ products: Product [0..*]  (M-N)",
    "+ created_at: datetime",
], ["+ add_product(product): void",
    "+ remove_product(product): void",
    "+ has_product(product): bool"], stereotype="favorites")

cls("Order", "Order", X1, 720, [
    "+ id: BigInt {PK}",
    "+ user: User {FK}",
    "+ status: OrderStatus",
    "+ delivery_status: DeliveryStatus",
    "+ total_amount: Decimal(14,2)",
    "+ payment_method: PaymentMethod",
    "+ shipping_carrier: ShippingCarrier",
    "+ recipient_name: str[100]",
    "+ shipping_address: str[255]",
    "+ recipient_phone: str[15]",
    "+ created_at: datetime",
], stereotype="orders")

cls("OrderItem", "OrderItem", X2, 720, [
    "+ id: BigInt {PK}",
    "+ order: Order {FK}",
    "+ product: Product {FK}",
    "+ quantity: int",
    "+ unit_price: Decimal(12,2)  (giá lúc mua)",
], ["+ /line_total: Decimal"], stereotype="orders")

cls("Review", "Review", X2, 1100, [
    "+ id: BigInt {PK}",
    "+ product: Product {FK}",
    "+ user: User {FK}",
    "+ order_item: OrderItem {FK}",
    "+ rating: int (1..5)",
    "+ content: text",
    "+ is_anonymous: bool = false",
    "+ sentiment: Sentiment",
    "+ sentiment_confidence: float [0..1]",
    "+ created_at: datetime",
    "{unique (user, product)}",
], ["+ /display_name: str"], stereotype="reviews")

cls("ReviewMedia", "ReviewMedia", X3, 1330, [
    "+ id: BigInt {PK}",
    "+ review: Review {FK}",
    "+ file: File",
    "+ media_type: MediaType",
], stereotype="reviews")

cls("Category", "Category", X3, 40, [
    "+ id: BigInt {PK}",
    "+ name: str[100] {unique}",
    "+ slug: str[120] {unique}",
    "+ created_at: datetime",
], ["+ save(): void  (tự sinh slug)"], stereotype="products")

cls("Product", "Product", X3, 330, [
    "+ id: BigInt {PK}",
    "+ category: Category {FK}",
    "+ created_by: User {FK} [0..1]",
    "+ name: str[200]",
    "+ slug: str[220] {unique}",
    "+ description: text",
    "+ price: Decimal(12,2)",
    "+ stock_quantity: int = 0",
    "+ gender: Gender = unisex",
    "+ image: Image [0..1]",
    "+ is_active: bool = true",
    "+ sku: str[64]",
    "+ specs: JSON",
    "+ care_instructions: text",
    "+ created_at: datetime",
    "+ updated_at: datetime",
], ["+ save(): void  (tự sinh slug)",
    "+ /is_in_stock: bool",
    "+ /description_intro: str",
    "+ /description_bullets: list[str]"], stereotype="products")

cls("ProductImage", "ProductImage", X4, 330, [
    "+ id: BigInt {PK}",
    "+ product: Product {FK}",
    "+ image: Image",
    "+ position: int = 0",
], stereotype="products")

cls("GlassesOverlay", "GlassesOverlay", X4, 620, [
    "+ id: BigInt {PK}",
    "+ product: Product {FK, unique}",
    "+ image: Image  (PNG trong suốt)",
    "+ width_ratio: float = 1.6",
    "+ vertical_offset: float = 0.0",
    "+ created_at: datetime",
    "+ updated_at: datetime",
], stereotype="tryon")

# enumeration (models.TextChoices) — tham chiếu bằng tên kiểu trong thuộc tính
ey = 40
for name, vals in [
    ("Gender", ["nu", "nam", "unisex"]),
    ("OrderStatus", ["DELIVERED", "CANCELLED"]),
    ("DeliveryStatus", ["PENDING", "IN_TRANSIT", "DELIVERED", "FAILED"]),
    ("PaymentMethod", ["COD", "MOMO", "CARD"]),
    ("ShippingCarrier", ["GHN", "GHTK", "SPX", "VIETTEL_POST", "JT"]),
    ("Sentiment", ["POS", "NEU", "NEG"]),
    ("MediaType", ["image", "video"]),
    ("TransactionType", ["DEPOSIT", "PAYMENT"]),
]:
    ey += cls("enum_" + name, name, X5, ey, vals, stereotype="enumeration", **EN) + 24

# ---------------------------------------------------------------- quan hệ
edge("User", "AbstractUser", "inherit")
edge("Category", "Product", "assoc", "1", "0..*")
edge("User", "Product", "assoc", "0..1", "0..*", "created_by",
     exit=(1, 0.1), entry=(0, 0.2), points=[(440, 484), (440, 390), (1300, 390), (1300, 424)])
edge("Product", "ProductImage", "comp", "1", "0..*")
edge("Product", "GlassesOverlay", "comp", "1", "0..1", exit=(1, 0.62), entry=(0, 0.3))
edge("User", "Cart", "assoc", "1", "0..1", exit=(0.85, 0), entry=(0, 0.5),
     points=[(329, 430), (420, 430), (420, 154)])
edge("Cart", "CartItem", "comp", "1", "0..*")
edge("CartItem", "Product", "assoc", "0..*", "1", exit=(1, 0.5), entry=(0, 0.05))
edge("User", "Favorite", "assoc", "1", "0..1", exit=(1, 0.6), entry=(0, 0.5))
edge("Favorite", "Product", "assoc", "0..*", "0..*", exit=(1, 0.3), entry=(0, 0.3))
edge("User", "Order", "assoc", "1", "0..*", exit=(1, 0.9), entry=(0, 0.2))
edge("Order", "OrderItem", "comp", "1", "1..*", exit=(1, 0.2), entry=(0, 0.3))
edge("OrderItem", "Product", "assoc", "0..*", "1", exit=(1, 0.3), entry=(0, 0.6))
edge("OrderItem", "Review", "assoc", "1", "0..1", exit=(0.5, 1), entry=(0.5, 0))
edge("Product", "Review", "assoc", "1", "0..*", exit=(0.25, 1), entry=(1, 0.2))
edge("User", "Review", "assoc", "1", "0..*", exit=(0.5, 1), entry=(0, 0.5),
     points=[(210, 1010), (400, 1010), (400, 1290)])
edge("Review", "ReviewMedia", "comp", "1", "0..*", exit=(1, 0.8), entry=(0, 0.5))
edge("User", "Wallet", "assoc", "1", "0..1", exit=(0.15, 1), entry=(0.15, 0))
edge("Wallet", "Transaction", "comp", "1", "0..*")

note(X4, 940, 420, 130,
     "Ghi chú\n"
     "◆ Composition: xoá lớp toàn thể thì xoá luôn lớp thành phần (on_delete=CASCADE).\n"
     "△ Kế thừa: User kế thừa AbstractUser của Django.\n"
     "/tên: thuộc tính dẫn xuất (@property).\n"
     "Product.created_by: SET_NULL khi xoá User.\n"
     "Cart: có user (thành viên) hoặc session_key (khách vãng lai).")

xml = ('<mxfile host="app.diagrams.net" agent="Claude Code" version="27.0.0" type="device">'
       '<diagram id="astraea-class" name="Astraea Class Diagram">'
       '<mxGraphModel dx="2600" dy="1700" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
       'fold="1" page="1" pageScale="1" pageWidth="2520" pageHeight="1700" math="0" shadow="0"><root>'
       '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>')
out = Path(__file__).resolve().parent.parent / "Astraea_ClassDiagram.drawio"
out.write_text(xml, encoding="utf-8")
print("Đã ghi", out)
