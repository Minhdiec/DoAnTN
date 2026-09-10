"""
Model cho app "reviews".

Review là đánh giá của một User cho một Product, BẮT BUỘC phải gắn với một
OrderItem làm "bằng chứng đã mua" (đơn hàng chứa OrderItem đó phải đã giao
thành công - kiểm tra ở view lúc tạo đánh giá, xem reviews/views.py).

Nhãn cảm xúc (sentiment/sentiment_confidence) được mô hình học máy tự động
gán khi lưu đánh giá (xem reviews/ml/sentiment.py), KHÔNG do người dùng nhập.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from orders.models import OrderItem
from products.models import Product


class Review(models.Model):
    class Sentiment(models.TextChoices):
        POSITIVE = "POS", "Tích cực"
        NEUTRAL = "NEU", "Trung lập"
        NEGATIVE = "NEG", "Tiêu cực"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Sản phẩm",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Người đánh giá",
    )

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name="Bằng chứng đã mua",
        help_text="Dòng đơn hàng (đã giao thành công) chứng minh người này đã mua sản phẩm.",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Số sao",
    )

    content = models.TextField(verbose_name="Nội dung đánh giá")

    is_anonymous = models.BooleanField(
        default=False,
        verbose_name="Ẩn danh",
        help_text="Bật thì KHÔNG hiển thị tên người dùng công khai (hệ thống vẫn biết là ai).",
    )

    sentiment = models.CharField(
        max_length=3,
        choices=Sentiment.choices,
        blank=True,
        verbose_name="Nhãn cảm xúc (AI)",
        help_text="Do mô hình học máy tự động gán khi lưu đánh giá.",
    )

    sentiment_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Độ tin cậy dự đoán",
        help_text="Xác suất lớn nhất trong 3 lớp - CHỈ dùng nội bộ/admin, không hiển thị cho khách.",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đánh giá")

    class Meta:
        verbose_name = "Đánh giá sản phẩm"
        verbose_name_plural = "Đánh giá sản phẩm"
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} đánh giá {self.product.name} ({self.rating}★)"

    @property
    def display_name(self):
        # Dùng trực tiếp trong template: {{ review.display_name }}
        return "Người dùng ẩn danh" if self.is_anonymous else self.user.username


class ReviewMedia(models.Model):
    """
    Ảnh/video đính kèm một đánh giá. Quan hệ Một-Nhiều: một đánh giá có thể
    có nhiều ảnh/video.
    """

    class MediaType(models.TextChoices):
        IMAGE = "image", "Ảnh"
        VIDEO = "video", "Video"

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="media",
        verbose_name="Đánh giá",
    )

    file = models.FileField(upload_to="reviews/%Y/%m/", verbose_name="File")

    media_type = models.CharField(
        max_length=5,
        choices=MediaType.choices,
        verbose_name="Loại file",
    )

    class Meta:
        verbose_name = "Ảnh/video đánh giá"
        verbose_name_plural = "Ảnh/video đánh giá"

    def __str__(self):
        return f"{self.get_media_type_display()} của đánh giá #{self.review_id}"
