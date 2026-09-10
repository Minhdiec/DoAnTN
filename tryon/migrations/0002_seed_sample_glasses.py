# Data migration: seed 2 bản ghi GlassesOverlay mẫu để có dữ liệu test ngay
# khi chạy thử tính năng thử kính ảo (xem CLAUDE_PROGRESS.md mục 24, Bước A).
#
# Gắn vào 2 trong 3 sản phẩm hiện có trong catalog demo (Incantation, Mythic,
# Impossible - xem mục 10 CLAUDE_PROGRESS.md), dùng đúng 2 ảnh PNG nền trong
# suốt người dùng đã tự tách nền sẵn trong media/tryon/glasses/ (Jasmin
# 01(BL)_f.png và Vanta 02_f.png - xem mục 14). Sản phẩm "Impossible" CỐ Ý
# chưa có ảnh AR (chỉ có 2 ảnh PNG thật, chưa có ảnh thứ 3) - trang chi tiết
# của nó sẽ ẩn nút "Thử kính ảo" cho tới khi có ảnh mới, không phải lỗi.
#
# Dùng RunPython (không phải fixture) để tra sản phẩm theo SLUG thay vì ID
# cứng - an toàn hơn nếu ID khác nhau giữa các máy/lần seed lại catalog.
from django.db import migrations

# Khớp ĐÚNG tên file vật lý đang nằm trong media/tryon/glasses/ (đã kiểm tra
# bằng lệnh "ls" trước khi viết migration này, không đoán).
SEED_DATA = [
    {"product_slug": "incantation-black", "image_name": "tryon/glasses/Jasmin 01(BL)_f.png"},
    {"product_slug": "mythic-gold-blue-light-lens", "image_name": "tryon/glasses/Vanta 02_f.png"},
]


def seed_glasses_overlay(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    GlassesOverlay = apps.get_model("tryon", "GlassesOverlay")

    for entry in SEED_DATA:
        try:
            product = Product.objects.get(slug=entry["product_slug"])
        except Product.DoesNotExist:
            # Không có sản phẩm này (ví dụ chạy trên DB khác đã seed catalog
            # khác) - bỏ qua thay vì làm hỏng migrate của người khác.
            continue
        GlassesOverlay.objects.get_or_create(
            product=product,
            defaults={"image": entry["image_name"]},
        )


def remove_glasses_overlay(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    GlassesOverlay = apps.get_model("tryon", "GlassesOverlay")
    slugs = [entry["product_slug"] for entry in SEED_DATA]
    GlassesOverlay.objects.filter(product__slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tryon", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_glasses_overlay, remove_glasses_overlay),
    ]
