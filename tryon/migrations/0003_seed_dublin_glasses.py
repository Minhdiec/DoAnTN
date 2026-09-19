# Data migration: thêm GlassesOverlay cho sản phẩm "Dublin" (mục 37 -
# CLAUDE_PROGRESS.md, kính Oval lấy từ carfia.com). Người dùng tự chỉnh sửa/
# xuất ảnh chính diện "Dublin.png" và bỏ vào media/tryon/glasses/, NHƯNG ảnh
# đó chỉ có 3 kênh (BGR thường, KHÔNG có kênh alpha) - GlassesOverlay bắt
# buộc PNG RGBA nền trong suốt (xem tryon/vision.py::GlassesOverlay.__init__)
# nên không dùng thẳng được.
#
# Đã tự tách nền bằng ngưỡng độ sáng (nền ảnh gốc là trắng THUẦN 255, gọng
# kính nằm hẳn trong khoảng 198-221 - có khoảng trống rõ giữa 2 vùng nên
# ngưỡng mềm 225-245 tách sạch, không cần công cụ AI tách nền ngoài) -> lưu
# thành "Dublin_f.png" (đúng quy ước hậu tố "_f" như 2 mẫu có sẵn). Đã kiểm
# tra: GlassesOverlay._find_lens_anchors tự tìm được đúng 2 tâm tròng kính
# (chế độ TỰ ĐỘNG hoạt động, không cần chỉnh width_ratio/vertical_offset).
from django.db import migrations

PRODUCT_SLUG = "dublin"
IMAGE_NAME = "tryon/glasses/Dublin_f.png"


def seed_dublin_glasses(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    GlassesOverlay = apps.get_model("tryon", "GlassesOverlay")

    try:
        product = Product.objects.get(slug=PRODUCT_SLUG)
    except Product.DoesNotExist:
        return

    GlassesOverlay.objects.get_or_create(
        product=product,
        defaults={"image": IMAGE_NAME},
    )


def remove_dublin_glasses(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    GlassesOverlay = apps.get_model("tryon", "GlassesOverlay")
    GlassesOverlay.objects.filter(product__slug=PRODUCT_SLUG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tryon", "0002_seed_sample_glasses"),
    ]

    operations = [
        migrations.RunPython(seed_dublin_glasses, remove_dublin_glasses),
    ]
