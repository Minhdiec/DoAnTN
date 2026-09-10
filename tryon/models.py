"""
Model cho app "tryon" (thử kính ảo qua webcam).

Chỉ có một model duy nhất: GlassesOverlay - lưu ảnh PNG kính (nền trong
suốt) dùng để dán lên mặt người dùng, gắn với đúng một Product. Quan hệ là
OneToOne (Một-Một, không phải Foreign Key Một-Nhiều) vì mỗi sản phẩm kính
chỉ cần đúng MỘT ảnh AR đại diện cho nó (xem CLAUDE_PROGRESS.md mục 2,
quyết định #3) - khác với ProductImage (Một-Nhiều) vốn dùng cho ảnh gallery
chụp thật, không liên quan tới model này.

CỐ Ý không sửa model Product/ProductImage của app "products" đang chạy ổn
định - GlassesOverlay đứng độc lập trong app riêng, chỉ tham chiếu tới
Product qua khóa ngoại.
"""

from django.db import models

from products.models import Product


class GlassesOverlay(models.Model):
    """
    Dữ liệu AR của một sản phẩm kính: ảnh PNG nền trong suốt + 2 số hiệu
    chỉnh dùng khi thuật toán KHÔNG tự động căn được (chế độ dự phòng của
    GlassesOverlay bên prototype/tryon_demo.py - xem CLAUDE_PROGRESS.md mục
    13, "Bước A"). Ở chế độ tự động, 2 số này không được dùng tới, nhưng vẫn
    giữ lại làm phương án dự phòng khi ảnh PNG không tìm được tâm 2 tròng
    kính đáng tin cậy (gọng quá mảnh, ảnh không đối xứng...).
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="glasses_overlay",
        verbose_name="Sản phẩm",
        help_text="Sản phẩm kính mà ảnh AR này đại diện cho.",
    )

    image = models.ImageField(
        upload_to="tryon/glasses/",
        verbose_name="Ảnh kính (PNG nền trong suốt)",
        help_text="Ảnh chụp thẳng mặt, nền trong suốt (kênh alpha), dùng để dán lên mặt qua webcam.",
    )

    width_ratio = models.FloatField(
        default=1.6,
        verbose_name="Tỉ lệ bề rộng (chế độ dự phòng)",
        help_text=(
            "CHỈ dùng khi thuật toán không tự tìm được tâm 2 tròng kính trong ảnh. "
            "Bề rộng kính hiển thị = khoảng cách 2 mắt × số này."
        ),
    )

    vertical_offset = models.FloatField(
        default=0.0,
        verbose_name="Độ lệch dọc (chế độ dự phòng)",
        help_text=(
            "CHỈ dùng ở chế độ dự phòng. Độ lệch dọc của tâm kính so với trung điểm 2 mắt, "
            "tính theo tỉ lệ khoảng cách 2 mắt (dương = xuống dưới)."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật gần nhất")

    class Meta:
        verbose_name = "Ảnh kính AR"
        verbose_name_plural = "Ảnh kính AR (thử kính ảo)"
        ordering = ["product__name"]

    def __str__(self):
        return f"Ảnh AR của {self.product.name}"
