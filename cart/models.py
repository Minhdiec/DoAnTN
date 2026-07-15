"""
Model cho app "cart".

Giống Wishlist/Wallet, mỗi User sở hữu đúng một Cart (quan hệ OneToOneField -
Một-Một). Bên trong Cart chứa nhiều CartItem, mỗi CartItem gắn với một
Product cụ thể kèm số lượng - đây là quan hệ Một-Nhiều giữa Cart và CartItem,
và quan hệ Một-Nhiều giữa Product và CartItem (một sản phẩm có thể nằm trong
giỏ hàng của nhiều người dùng khác nhau, ở nhiều CartItem khác nhau).
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from products.models import Product


class Cart(models.Model):
    """
    Giỏ hàng của một người dùng.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="Người dùng",
        help_text="Mỗi người dùng chỉ có đúng một giỏ hàng.",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Giỏ hàng"
        verbose_name_plural = "Giỏ hàng"

    def __str__(self):
        return f"Giỏ hàng của {self.user.username}"

    def add_product(self, product, quantity=1):
        # Nếu sản phẩm đã có sẵn trong giỏ, cộng dồn số lượng thay vì tạo
        # dòng mới; luôn giới hạn (clamp) số lượng không vượt quá tồn kho
        # hiện có để không cho đặt nhiều hơn số hàng thực tế đang có.
        item, _ = self.items.get_or_create(product=product, defaults={"quantity": 0})
        new_quantity = item.quantity + quantity
        item.quantity = min(new_quantity, product.stock_quantity) if product.stock_quantity else new_quantity
        item.save(update_fields=["quantity"])
        return item

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        # Luôn cộng dồn bằng Decimal (không dùng float) để không phát sinh
        # sai số làm tròn khi tính tổng tiền giỏ hàng.
        return sum(
            (item.line_total for item in self.items.all()),
            Decimal("0.00"),
        )


class CartItem(models.Model):
    """
    Một dòng sản phẩm trong giỏ hàng: sản phẩm nào, số lượng bao nhiêu.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Giỏ hàng",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="Sản phẩm",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Số lượng",
    )

    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian thêm vào giỏ")

    class Meta:
        verbose_name = "Sản phẩm trong giỏ hàng"
        verbose_name_plural = "Sản phẩm trong giỏ hàng"
        unique_together = ("cart", "product")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def line_total(self):
        return self.product.price * self.quantity
