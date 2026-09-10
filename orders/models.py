"""
Model cho app "orders".

Đây là "bằng chứng đã mua" của toàn hệ thống: khi người dùng bấm "Đặt hàng"
ở giỏ hàng, giỏ hàng (Cart/CartItem - tạm, có thể sửa/xóa) được "đóng băng"
lại thành một Order kèm nhiều OrderItem (từng dòng sản phẩm, LƯU LẠI giá tại
thời điểm mua, vì giá sản phẩm có thể thay đổi sau này mà đơn hàng cũ không
được đổi theo).

LƯU Ý: đồ án này KHÔNG mô phỏng quy trình vận chuyển nhiều trạng thái (chờ
xác nhận -> đang giao -> giao thành công...). Để đơn giản, MỌI đơn hàng vừa
đặt (thanh toán qua ví thành công) được coi là đã giao thành công ngay lập
tức. Trường "status" chỉ có 2 giá trị: đã giao (mặc định) và đã hủy - người
mua có thể tự hủy đơn đã đặt (orders/views.py::cancel_order), khi đó tồn
kho của từng sản phẩm trong đơn được TỰ ĐỘNG hoàn trả lại.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        DELIVERED = "DELIVERED", "Giao hàng thành công"
        CANCELLED = "CANCELLED", "Đã hủy"

    class PaymentMethod(models.TextChoices):
        COD = "COD", "Thanh toán khi nhận hàng (COD)"
        MOMO = "MOMO", "Ví MoMo"
        CARD = "CARD", "Thẻ ngân hàng"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Người mua",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DELIVERED,
        verbose_name="Trạng thái đơn hàng",
        help_text="Đồ án không mô phỏng vận chuyển nhiều bước - đơn mới đặt luôn ở trạng thái đã giao thành công, người mua có thể tự hủy sau đó.",
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Tổng tiền đơn hàng (VNĐ)",
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
        verbose_name="Hình thức thanh toán",
        help_text="Đồ án GIẢ LẬP bước thanh toán (chưa nối cổng thanh toán thật) - chỉ ghi lại hình thức người dùng chọn.",
    )

    recipient_name = models.CharField(
        max_length=100,
        default="",
        verbose_name="Tên người nhận",
    )

    shipping_address = models.CharField(
        max_length=255,
        default="",
        verbose_name="Địa chỉ nhận hàng",
        help_text="Bắt buộc nhập trước khi thanh toán - lưu lại đúng địa chỉ tại thời điểm đặt hàng (khác với địa chỉ mặc định trong hồ sơ, vì người dùng có thể đổi sau này).",
    )

    recipient_phone = models.CharField(
        max_length=15,
        default="",
        verbose_name="SĐT người nhận",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đặt hàng")

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Đơn #{self.pk} - {self.user.username}"


class OrderItem(models.Model):
    """
    Một dòng sản phẩm trong đơn hàng: sản phẩm nào, số lượng bao nhiêu, mua
    với giá bao nhiêu - đây chính là bằng chứng "đã mua sản phẩm X" mà app
    reviews sẽ cần tới khi cho phép đánh giá.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Đơn hàng",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Sản phẩm",
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Số lượng",
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Đơn giá lúc mua (VNĐ)",
        help_text="Giá sản phẩm tại thời điểm mua, không đổi theo giá hiện tại của sản phẩm.",
    )

    class Meta:
        verbose_name = "Sản phẩm trong đơn hàng"
        verbose_name_plural = "Sản phẩm trong đơn hàng"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
