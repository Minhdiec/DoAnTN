"""
Model cho app "favorites".

Mỗi người dùng (User) sở hữu đúng một "Danh sách yêu thích" (quan hệ
OneToOneField - Một-Một), và bên trong danh sách đó có thể chứa nhiều sản
phẩm khác nhau; đồng thời một sản phẩm cũng có thể được rất nhiều người
dùng khác nhau cùng yêu thích. Đây chính là quan hệ Many-to-Many (Nhiều-
Nhiều) được yêu cầu trong đề bài, và Django sẽ tự động tạo ra một bảng
trung gian (bảng nối) trong MySQL để lưu quan hệ này.
"""

from django.conf import settings
from django.db import models

from products.models import Product


class Favorite(models.Model):
    """
    Danh sách yêu thích của một người dùng.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Người dùng",
        help_text="Mỗi người dùng chỉ có đúng một danh sách yêu thích.",
    )

    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="favorited_by",
        verbose_name="Sản phẩm yêu thích",
        help_text="Các sản phẩm mà người dùng này đã thêm vào danh sách yêu thích.",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Danh sách yêu thích"
        verbose_name_plural = "Danh sách yêu thích"

    def __str__(self):
        return f"Danh sách yêu thích của {self.user.username}"

    def add_product(self, product):
        # Thêm một sản phẩm vào danh sách yêu thích. Nếu sản phẩm đã có sẵn
        # trong danh sách rồi, ManyToManyField.add() sẽ tự động bỏ qua,
        # không tạo ra bản ghi trùng lặp trong bảng trung gian.
        self.products.add(product)

    def remove_product(self, product):
        # Xóa một sản phẩm khỏi danh sách yêu thích. Nếu sản phẩm đó chưa
        # từng có trong danh sách, remove() cũng không báo lỗi gì cả.
        self.products.remove(product)

    def has_product(self, product):
        # Kiểm tra xem một sản phẩm đã có trong danh sách yêu thích hay
        # chưa, dùng để hiển thị đúng trạng thái nút "Yêu thích" trên giao diện.
        return self.products.filter(pk=product.pk).exists()
