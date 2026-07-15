"""
Management command: crawl thêm ảnh gallery + thông số kỹ thuật cho các sản
phẩm đã có sẵn trong DB, lấy từ đúng nguồn dữ liệu ban đầu của seed_products.sql
(intl.lespecs.com - một shop chạy nền tảng Shopify).

Vì sao dùng endpoint "<slug>.json" thay vì parse HTML:
Shopify công khai endpoint JSON cho mọi trang sản phẩm (thêm đuôi ".json" vào
URL), trả về đầy đủ ảnh + biến thể + tag mà không cần parse HTML (vốn dễ vỡ
khi theme đổi giao diện). Thông số kỹ thuật (kích thước gọng, chất liệu...)
hóa ra cũng nằm ngay trong "tags" dưới dạng "Key:Value" (ví dụ
"Frame Width:141"), nên không cần lấy thêm từ HTML nữa.

Cách chạy:
    python manage.py scrape_lespecs_details              # toàn bộ sản phẩm chưa có ảnh gallery
    python manage.py scrape_lespecs_details --limit 3     # thử nhanh 3 sản phẩm đầu
    python manage.py scrape_lespecs_details --slug <slug> # đúng 1 sản phẩm
    python manage.py scrape_lespecs_details --force       # crawl lại cả sản phẩm đã có ảnh
"""

import time

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from products.models import Product, ProductImage

SOURCE_URL_TEMPLATE = "https://intl.lespecs.com/products/{slug}.json"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ChuyenDeTN-hoc-tap-bot/1.0)"}
REQUEST_TIMEOUT = 15
DELAY_BETWEEN_PRODUCTS = 0.4

# Ánh xạ tên tag (viết thường) trên lespecs.com sang nhãn tiếng Việt hiển thị
# trên trang chi tiết sản phẩm. Giá trị thứ 2 là đơn vị (nếu có) để nối thêm
# vào sau con số, ví dụ "141" -> "141 mm".
SPEC_LABELS = {
    "frame width": ("Chiều rộng gọng", "mm"),
    "frame height": ("Chiều cao gọng", "mm"),
    "lens width": ("Chiều rộng tròng kính", "mm"),
    "nose bridge": ("Cầu mũi", "mm"),
    "temple length": ("Chiều dài càng kính", "mm"),
    "frame material": ("Chất liệu gọng", None),
    "frame shape": ("Dáng gọng", None),
    "frame size": ("Cỡ gọng", None),
    "lens material": ("Chất liệu tròng kính", None),
    "frame colour": ("Màu gọng", None),
    "lens colour": ("Màu tròng kính", None),
    "uv protection": ("Chống tia UV", None),
    "warranty": ("Bảo hành", None),
}

# Các tag dạng "Có/Không" (Y/N) trên lespecs.com.
BOOLEAN_SPEC_LABELS = {
    "polarised": "Chống chói (phân cực)",
}

DEFAULT_CARE_INSTRUCTIONS = (
    "- Bảo quản kính trong túi/hộp đi kèm khi không sử dụng.\n"
    "- Lau tròng kính bằng khăn microfiber đi kèm, tránh dùng khăn giấy hoặc vải "
    "thô dễ gây trầy xước.\n"
    "- Không đặt kính úp mặt tròng kính xuống các bề mặt cứng.\n"
    "- Tránh để kính ở nơi có nhiệt độ cao (trong xe hơi đóng kín, gần nguồn nhiệt)."
)


def normalize_image_url(url):
    # Shopify hay trả URL dạng "//domain/..." (protocol-relative), trình
    # duyệt tự hiểu là https, nhưng requests thì cần URL đầy đủ.
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("http"):
        return url
    return f"https://{url}"


class Command(BaseCommand):
    help = "Crawl thêm ảnh gallery + thông số kỹ thuật cho Product từ intl.lespecs.com."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Chỉ xử lý tối đa N sản phẩm.")
        parser.add_argument("--slug", type=str, default=None, help="Chỉ xử lý đúng 1 sản phẩm theo slug.")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Crawl lại cả những sản phẩm đã có ảnh gallery (mặc định sẽ bỏ qua để chạy lại an toàn).",
        )

    def handle(self, *args, **options):
        queryset = Product.objects.all().order_by("id")
        if options["slug"]:
            queryset = queryset.filter(slug=options["slug"])
        if not options["force"]:
            queryset = queryset.filter(images__isnull=True)
        if options["limit"]:
            queryset = queryset[: options["limit"]]

        products = list(queryset)
        total = len(products)
        self.stdout.write(f"Sẽ xử lý {total} sản phẩm...")

        success_count = 0
        failure_count = 0
        for index, product in enumerate(products, start=1):
            try:
                image_count = self.scrape_one(product)
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"[{index}/{total}] OK: {product.slug} (+{image_count} ảnh)")
                )
            except Exception as exc:
                failure_count += 1
                self.stdout.write(self.style.WARNING(f"[{index}/{total}] LỖI ({product.slug}): {exc}"))
            time.sleep(DELAY_BETWEEN_PRODUCTS)

        self.stdout.write(self.style.SUCCESS(f"Hoàn tất: {success_count} thành công, {failure_count} lỗi."))

    def scrape_one(self, product):
        response = requests.get(
            SOURCE_URL_TEMPLATE.format(slug=product.slug),
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()["product"]

        # Ảnh đầu tiên trên lespecs.com trùng với ảnh chính (product.image) đã
        # tải sẵn lúc seed dữ liệu, nên chỉ lấy các ảnh còn lại làm gallery.
        image_urls = [image["src"] for image in data.get("images", [])]
        gallery_urls = image_urls[1:] if len(image_urls) > 1 else image_urls

        product.images.all().delete()
        for position, image_url in enumerate(gallery_urls, start=1):
            image_response = requests.get(
                normalize_image_url(image_url), headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
            )
            image_response.raise_for_status()
            product_image = ProductImage(product=product, position=position)
            product_image.image.save(
                f"{product.slug}-{position}.jpg", ContentFile(image_response.content), save=True
            )

        variants = data.get("variants") or []
        if variants and variants[0].get("sku"):
            product.sku = variants[0]["sku"]

        # Endpoint "<slug>.json" trả "tags" dạng 1 chuỗi nối bằng dấu phẩy
        # (khác với JSON nhúng trong HTML là 1 mảng), nên phải tự tách ra.
        raw_tags = data.get("tags", [])
        tag_list = raw_tags.split(",") if isinstance(raw_tags, str) else raw_tags

        specs = {}
        for tag in tag_list:
            tag = tag.strip()
            if ":" not in tag:
                continue
            raw_key, _, raw_value = tag.partition(":")
            key = raw_key.strip().lower()
            value = raw_value.strip()
            if not value or "online" in key:
                continue
            if key in SPEC_LABELS:
                label, unit = SPEC_LABELS[key]
                specs[label] = f"{value} {unit}" if unit else value
            elif key in BOOLEAN_SPEC_LABELS:
                specs[BOOLEAN_SPEC_LABELS[key]] = "Có" if value.upper().startswith("Y") else "Không"
        if specs:
            product.specs = specs

        if not product.care_instructions:
            product.care_instructions = DEFAULT_CARE_INSTRUCTIONS

        product.save(update_fields=["sku", "specs", "care_instructions", "updated_at"])
        return len(gallery_urls)
