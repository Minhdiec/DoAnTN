"""
Management command: nhập thêm sản phẩm KÍNH CẬN/KÍNH GỌNG THÔNG THƯỜNG từ
https://www.carfia.com/collections/eyeglasses (shop chạy Shopify, giống nguồn
lespecs.com của scrape_lespecs_details) - KHÔNG lấy kính mát.

Những gì lệnh này làm:
    1. Tải danh sách sản phẩm qua endpoint JSON công khai của Shopify
       (/collections/<handle>/products.json).
    2. Loại toàn bộ kính mát: handle chứa "sunglass", tên đuôi "-RX" (kính mát
       có độ), product_type khác "Eyeglasses", tag Polarized/Driving...
    3. Xác định DÁNG GỌNG theo đúng các bộ lọc dáng của carfia (collection
       square-eyeglasses, oval-eyeglasses...), nếu không có thì dựa vào tag/mô
       tả - mỗi dáng là 1 Category. Chỉ nhập 3 dáng Square/Oval/Round.
    4. Mỗi dòng kính (Albany, Kenosha, ...) chỉ lấy 1 phiên bản màu đại diện,
       tránh trang chủ toàn cùng 1 mẫu khác màu.
    5. Ảnh: chỉ lấy ảnh sản phẩm ở các góc (front/angle/side/detail...), BỎ ảnh
       người mẫu (model/lifestyle) và ảnh thông số (size chart).
    6. Mã SKU lấy đúng mã biến thể của carfia (VD CA5352-FC13).
    7. Tự tách nền trắng ảnh chính diện thành PNG trong suốt để thử kính ảo;
       chỉ gắn GlassesOverlay khi thuật toán tìm được đúng 2 tâm tròng kính.

Lệnh idempotent: sản phẩm đã có (trùng SKU) sẽ được bỏ qua.

Cách chạy:
    python manage.py import_carfia_eyeglasses
    python manage.py import_carfia_eyeglasses --limit 5
    python manage.py import_carfia_eyeglasses --dry-run
"""

import hashlib
import io
import re
import time
from collections import Counter, defaultdict
from decimal import Decimal

import cv2
import numpy as np
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from PIL import Image

from products.models import Category, Product, ProductImage
from tryon.models import GlassesOverlay
from tryon.vision import GlassesOverlay as GlassesRenderer

from .scrape_lespecs_details import DEFAULT_CARE_INSTRUCTIONS

BASE_URL = "https://www.carfia.com"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Astraea-do-an-bot/1.0)"}
REQUEST_TIMEOUT = 30

# Tỉ giá quy đổi giá USD của carfia sang VNĐ - cùng mức đã dùng cho kính
# Dublin (33,99 USD -> 1.890.000đ), làm tròn tới 10.000đ.
USD_TO_VND = Decimal("55600")

# Collection dáng gọng trên carfia -> tên Category trong Astraea. Cửa hàng
# chỉ bán 3 dáng: Square, Oval, Round - dòng kính dáng khác bị bỏ qua.
SHAPE_COLLECTIONS = {
    "square-eyeglasses": "Square",
    "oval-eyeglasses": "Oval",
    "round-eyeglasses": "Round",
    "rectangle-eyeglasses": "Rectangle",
    "cat-eye-glasses": "Cat-Eye",
}
ALLOWED_SHAPES = {"Square", "Oval", "Round"}

SHAPE_TAGS = {
    "square": "Square", "square frame": "Square", "square frames": "Square",
    "square-frames": "Square", "square eyeglasses": "Square",
    "oval": "Oval", "oval eyeglasses": "Oval",
    "round": "Round", "round glasses": "Round", "round eyeglasses": "Round",
    "rectangle": "Rectangle", "rectangular eyeglasses": "Rectangle",
    "cat-eye": "Cat-Eye",
}

SHAPE_LABELS_VI = {
    "Square": "vuông",
    "Oval": "oval",
    "Round": "tròn",
    "Rectangle": "chữ nhật",
    "Cat-Eye": "mắt mèo",
}

SUNGLASSES_TAGS = {"polarized", "driving sunglasses", "driving glasses", "sunglasses"}

COLOR_VI = {
    "tortoise": "Đồi mồi", "black": "Đen", "brown": "Nâu", "gold": "Vàng gold",
    "grey": "Xám", "gray": "Xám", "green": "Xanh lá", "clear": "Trong suốt",
    "multicolor": "Nhiều màu", "blue": "Xanh dương", "striped": "Sọc vân",
    "yellow": "Vàng", "pink": "Hồng", "coffee": "Nâu cà phê", "silver": "Bạc",
    "tea-brown": "Nâu trà", "beige": "Be", "orange": "Cam", "white": "Trắng",
    "green-black": "Xanh đen", "red": "Đỏ",
}

# Ảnh cần lấy / cần bỏ, nhận biết qua tên file trên CDN của carfia.
VIEW_KEYWORDS = ("front", "angle", "angla", "side", "detail", "three-quarter", "fly", "flod", "fold", "top")
SKIP_KEYWORDS = ("model", "lifestyle", "size", "chart", "wear")

MEASURE_PATTERNS = [
    ("Chiều rộng gọng", r"frame\s*width"),
    ("Chiều rộng tròng kính", r"lens\s*width"),
    ("Chiều cao tròng kính", r"lens\s*height"),
    ("Cầu mũi", r"(?:nose\s*)?bridge(?:\s*width)?"),
    ("Chiều dài càng kính", r"(?:temple|arm)(?:\s*length)?"),
]

MAX_GALLERY_IMAGES = 5
MAX_IMAGE_SIDE = 1400


def _fetch_collection(handle):
    products = []
    for page in range(1, 10):
        url = f"{BASE_URL}/collections/{handle}/products.json?limit=250&page={page}"
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        batch = resp.json().get("products", [])
        if not batch:
            break
        products.extend(batch)
    return products


def _is_sunglasses(p):
    if p.get("product_type") != "Eyeglasses":
        return True
    if "sunglass" in p["handle"] or p["title"].strip().upper().endswith("-RX"):
        return True
    return any(t.lower() in SUNGLASSES_TAGS for t in p.get("tags", []))


def _family(title):
    return re.split(r"[- ]", title.strip())[0].lower()


def _image_name(src):
    return src.split("/")[-1].split("?")[0].lower()


def _pick_images(product):
    """Trả về (ảnh chính diện, [ảnh góc khác]) - chỉ ảnh sản phẩm, bỏ ảnh
    người mẫu / ảnh bảng size. Trùng nội dung (cùng tên khác đuôi jpg/webp)
    chỉ lấy 1."""
    seen = set()
    views = []
    for img in product.get("images", []):
        name = _image_name(img["src"])
        stem = name.rsplit(".", 1)[0]
        if stem in seen:
            continue
        if any(k in name for k in SKIP_KEYWORDS):
            continue
        if not any(k in name for k in VIEW_KEYWORDS):
            continue
        seen.add(stem)
        views.append(img["src"])
    front = next((s for s in views if "front" in _image_name(s)), None)
    if front is None:
        return None, []
    others = [s for s in views if s != front][:MAX_GALLERY_IMAGES]
    return front, others


def _download(src):
    resp = requests.get(src, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    return img


def _is_product_shot(img):
    return (np.asarray(img).min(axis=2) > 235).mean() >= 0.3


def _to_jpeg_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def _make_overlay_png(img):
    """Tách nền trắng -> PNG RGBA cắt sát viền. Cùng cách đã làm với
    Dublin_f.png (CLAUDE_PROGRESS.md mục 41): ảnh carfia chụp trên nền trắng,
    dùng ngưỡng mềm độ sáng; vùng tròng kính trong suốt cũng thành lỗ hổng
    nên thuật toán tự tìm được tâm 2 tròng kính. Trả về None nếu ảnh không
    dùng được cho thử kính ảo."""
    rgb = np.asarray(img).astype(np.float32)
    # "Độ trắng" = kênh tối nhất; nền trắng thuần ~255 ở cả 3 kênh.
    whiteness = rgb.min(axis=2)
    alpha = np.clip((245.0 - whiteness) / (245.0 - 225.0), 0.0, 1.0)
    alpha_u8 = (alpha * 255).astype(np.uint8)
    # Xoá các chấm nhiễu nhỏ (bụi, bóng mờ) ngoài gọng kính.
    num, labels, stats, _ = cv2.connectedComponentsWithStats((alpha_u8 > 10).astype(np.uint8), connectivity=8)
    if num <= 1:
        return None
    biggest = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    min_keep = stats[biggest, cv2.CC_STAT_AREA] * 0.01
    keep = np.zeros(num, dtype=bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_keep
    alpha_u8[~keep[labels]] = 0

    ys, xs = np.where(alpha_u8 > 10)
    if len(xs) == 0:
        return None
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    # Ảnh chính diện của kính luôn rộng hơn cao nhiều; ảnh chụp nghiêng/gập
    # không phù hợp để dán lên mặt.
    if w < h * 1.8:
        return None
    bgr = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    bgra = np.dstack([bgr, alpha_u8])[y0:y1 + 1, x0:x1 + 1]
    anchors = GlassesRenderer._find_lens_anchors(bgra)
    if anchors is None:
        return None
    (lx, ly), (rx, ry) = anchors
    # 2 tâm tròng phải nằm 2 bên, gần cùng độ cao, cách nhau hợp lý.
    if not (lx < w * 0.45 and rx > w * 0.55 and abs(ly - ry) < h * 0.15):
        return None
    ok, png = cv2.imencode(".png", bgra)
    return png.tobytes() if ok else None


def _price_vnd(usd):
    vnd = Decimal(usd) * USD_TO_VND
    return (vnd / 10000).quantize(Decimal("1")) * 10000


def _stock_for(sku):
    return 12 + int(hashlib.md5(sku.encode()).hexdigest(), 16) % 29


def _gender(tags):
    low = {t.lower() for t in tags}
    has_men = "men" in low or "men eyeglasses" in low
    has_women = "women" in low or "women eyeglasses" in low or "womens-eyeglasses" in low
    if has_men and not has_women:
        return Product.Gender.MALE
    if has_women and not has_men:
        return Product.Gender.FEMALE
    return Product.Gender.UNISEX


def _measurements(body_html):
    text = re.sub(r"<[^>]+>", " ", body_html or "")
    out = {}
    for label, pattern in MEASURE_PATTERNS:
        m = re.search(pattern + r"\s*:?\s*(\d{2,3})\s*mm", text, re.IGNORECASE)
        if m:
            out[label] = f"{m.group(1)} mm"
    return out


def _material(tags, body_html):
    low = " ".join(tags).lower() + " " + (body_html or "").lower()
    if "acetate" in low:
        return "Acetate"
    if "titanium" in low:
        return "Titanium"
    if "metal" in low:
        return "Kim loại"
    return "Nhựa TR90"


def _rim(tags):
    low = {t.lower() for t in tags}
    if "rimless" in low or "frameless glasses" in low:
        return "Không viền"
    if "semi-rimless" in low:
        return "Nửa viền"
    return "Viền kín"


def _build_description(name, shape, color_vi, material, rim, gender, measures):
    shape_vi = SHAPE_LABELS_VI[shape]
    who = {"nam": "phái nam", "nu": "phái nữ"}.get(gender, "cả nam và nữ")
    intro = (
        f"Gọng kính {name} mang dáng {shape_vi} {rim.lower()}, màu {color_vi.lower()}, "
        f"làm từ chất liệu {material.lower() if material != 'Acetate' else 'acetate'} nhẹ và bền. "
        f"Thiết kế tối giản dễ phối đồ, phù hợp cho {who} khi đi học, đi làm hay dạo phố."
    )
    bullets = [
        f"Dáng {shape_vi} {'tôn đường nét khuôn mặt, hợp mặt tròn và mặt trái xoan' if shape in ('Square', 'Rectangle') else 'mềm mại, hợp mặt vuông và mặt dài'}",
        f"Chất liệu {material} nhẹ, ôm mặt, đeo cả ngày không bị đau sống mũi",
        f"Kiểu {rim.lower()} giữ tròng kính chắc chắn",
        "Lắp được tròng cận, viễn, loạn, đa tròng hoặc tròng lọc ánh sáng xanh",
        "Hỗ trợ thử kính ảo qua webcam ngay trên website trước khi mua",
    ]
    if measures.get("Chiều rộng gọng"):
        bullets.insert(3, f"Chiều rộng gọng {measures['Chiều rộng gọng']}, vừa với đa số khuôn mặt người Việt")
    return intro + "\n" + "\n".join(f"- {b}" for b in bullets)


class Command(BaseCommand):
    help = "Nhập kính gọng thông thường (không lấy kính mát) từ carfia.com kèm dáng gọng, ảnh, SKU, ảnh thử kính."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Chỉ nhập tối đa N dòng kính")
        parser.add_argument("--dry-run", action="store_true", help="Chỉ in danh sách sẽ nhập, không ghi DB")

    def handle(self, *args, **opts):
        self.stdout.write("Đang tải danh sách kính từ carfia.com ...")
        eyeglasses = [p for p in _fetch_collection("eyeglasses") if not _is_sunglasses(p)]
        self.stdout.write(f"  {len(eyeglasses)} sản phẩm kính gọng (đã loại kính mát)")

        shape_by_handle = defaultdict(set)
        for handle, shape in SHAPE_COLLECTIONS.items():
            for p in _fetch_collection(handle):
                shape_by_handle[p["handle"]].add(shape)

        families = defaultdict(list)
        for p in eyeglasses:
            families[_family(p["title"])].append(p)

        existing_skus = set(Product.objects.exclude(sku="").values_list("sku", flat=True))
        existing_families = {_family(n) for n in Product.objects.values_list("name", flat=True)}

        plan = []
        for fam, variants in families.items():
            if fam in existing_families:
                continue
            shape = self._family_shape(variants, shape_by_handle)
            if shape not in ALLOWED_SHAPES:
                continue
            # Chọn biến thể đầu tiên có đủ ảnh chính diện + ảnh góc khác.
            chosen = None
            for v in variants:
                front, others = _pick_images(v)
                if front and others:
                    chosen = (v, front, others)
                    break
            if chosen is None:
                continue
            v = chosen[0]
            sku = (v["variants"][0].get("sku") or "").strip().upper()
            if not sku or sku in existing_skus:
                continue
            plan.append((fam, shape, sku) + chosen)

        if opts["limit"]:
            plan = plan[: opts["limit"]]
        self.stdout.write(f"  Sẽ nhập {len(plan)} dòng kính")

        if opts["dry_run"]:
            for fam, shape, sku, v, front, others in plan:
                self.stdout.write(f"    {v['title']:<24} {shape:<10} {sku:<14} {len(others)} ảnh phụ")
            return

        created, overlays = 0, 0
        for fam, shape, sku, v, front, others in plan:
            try:
                has_overlay = self._import_one(shape, sku, v, front, others)
            except Exception as exc:  # 1 sản phẩm lỗi không làm hỏng cả đợt nhập
                self.stderr.write(f"  LỖI {v['title']}: {exc}")
                continue
            created += 1
            overlays += int(has_overlay)
            self.stdout.write(f"  + {v['title']} ({shape}, {sku}){' + ảnh thử kính' if has_overlay else ''}")
            time.sleep(0.3)

        self.stdout.write(self.style.SUCCESS(f"Xong: thêm {created} sản phẩm, {overlays} sản phẩm có ảnh thử kính ảo."))

    @staticmethod
    def _family_shape(variants, shape_by_handle):
        votes = Counter()
        for v in variants:
            votes.update(shape_by_handle.get(v["handle"], ()))
        if not votes:
            for v in variants:
                votes.update({SHAPE_TAGS[t.lower()] for t in v.get("tags", []) if t.lower() in SHAPE_TAGS})
        if not votes:
            for v in variants:
                text = re.sub(r"<[^>]+>", " ", v.get("body_html") or "").lower()
                for key, shape in (("cat-eye", "Cat-Eye"), ("rectangular", "Rectangle"), ("rectangle", "Rectangle"),
                                   ("square", "Square"), ("oval", "Oval"), ("round", "Round")):
                    if key in text:
                        votes[shape] += 1
                        break
        if not votes:
            return None
        # Carfia xếp nhiều mẫu oval vào cả "Round" lẫn "Oval" - Oval cụ thể hơn.
        if votes.get("Oval") and votes.get("Round"):
            return "Oval"
        return votes.most_common(1)[0][0]

    def _import_one(self, shape, sku, v, front_src, other_srcs):
        variant = v["variants"][0]
        color_raw = (variant.get("option2") or "").strip()
        color_vi = COLOR_VI.get(color_raw.lower(), color_raw.title() or "Nhiều màu")
        tags = v.get("tags", [])
        material = _material(tags, v.get("body_html"))
        rim = _rim(tags)
        gender = _gender(tags)
        measures = _measurements(v.get("body_html"))
        name = re.sub(r"\s*-\s*", " ", v["title"].strip())
        name = re.sub(r"\s+", " ", name)

        front_img = _download(front_src)
        # Một số ảnh người mẫu trên carfia vẫn đặt tên "detail"/"three-quarter"
        # - ảnh sản phẩm thật luôn chụp trên nền trắng nên loại ảnh có quá ít
        # điểm ảnh trắng.
        gallery = [img for img in (_download(src) for src in other_srcs) if _is_product_shot(img)]
        overlay_png = _make_overlay_png(front_img)

        specs = {
            "Màu gọng": color_vi,
            "Dáng gọng": shape,
            "Cỡ gọng": (variant.get("option1") or "M").strip(),
            "Chất liệu gọng": material,
            "Kiểu viền": rim,
        }
        specs.update(measures)
        if variant.get("grams"):
            specs["Trọng lượng"] = f"{variant['grams']} g"

        category, _ = Category.objects.get_or_create(name=shape)
        slug_base = slugify(name) or slugify(sku)
        slug = slug_base
        n = 2
        while Product.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{n}"
            n += 1

        with transaction.atomic():
            product = Product(
                category=category,
                name=name,
                slug=slug,
                description=_build_description(name, shape, color_vi, material, rim, gender, measures),
                price=_price_vnd(variant["price"]),
                stock_quantity=_stock_for(sku),
                gender=gender,
                sku=sku,
                specs=specs,
                care_instructions=DEFAULT_CARE_INSTRUCTIONS,
            )
            product.image.save(f"{slug}-front.jpg", ContentFile(_to_jpeg_bytes(front_img)), save=False)
            product.save()
            for i, img in enumerate(gallery, start=1):
                pi = ProductImage(product=product, position=i)
                pi.image.save(f"{slug}-{i}.jpg", ContentFile(_to_jpeg_bytes(img)), save=False)
                pi.save()
            if overlay_png:
                overlay = GlassesOverlay(product=product)
                overlay.image.save(f"{slug}_f.png", ContentFile(overlay_png), save=False)
                overlay.save()
        return overlay_png is not None
