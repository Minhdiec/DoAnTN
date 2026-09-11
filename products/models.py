"""
Model cho app "products".

Ở đây ta định nghĩa hai model chính:
    - Category: danh mục sản phẩm (ví dụ: "Điện thoại", "Laptop", "Thời trang").
    - Product: một sản phẩm cụ thể, luôn thuộc về một Category (quan hệ
      Foreign Key - Khóa ngoại, tức là quan hệ Một-Nhiều: một Category có
      thể có nhiều Product, nhưng mỗi Product chỉ thuộc về đúng một Category).

Giá tiền (price) được khai báo bằng DecimalField chứ KHÔNG dùng FloatField,
vì FloatField lưu số thực dưới dạng dấu phẩy động (binary floating point)
nên rất dễ bị sai số làm tròn (ví dụ 0.1 + 0.2 có thể ra 0.30000000000004).
DecimalField lưu số thập phân chính xác tuyệt đối, bắt buộc phải dùng cho
mọi giá trị liên quan đến tiền tệ.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """
    Danh mục sản phẩm. Dùng để nhóm các sản phẩm có cùng loại lại với nhau,
    giúp người dùng dễ dàng lọc/tìm kiếm sản phẩm theo nhóm trên trang chủ.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Tên danh mục",
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        verbose_name="Đường dẫn thân thiện",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Danh mục sản phẩm"
        verbose_name_plural = "Danh mục sản phẩm"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Nếu người quản trị chưa tự nhập slug, ta tự động sinh ra từ "name"
        # bằng hàm slugify (ví dụ "Điện Thoại" -> "dien-thoai").
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Một sản phẩm cụ thể được bày bán trên website.

    Quan hệ với Category là Foreign Key (Khóa ngoại - quan hệ Một-Nhiều):
    mỗi sản phẩm bắt buộc phải thuộc về một danh mục.
    Quan hệ với User (created_by) cũng là Foreign Key: ghi lại người quản
    trị/người bán nào đã tạo ra sản phẩm này, phục vụ việc truy vết sau này.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Danh mục",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_products",
        verbose_name="Người tạo",
    )

    name = models.CharField(
        max_length=200,
        verbose_name="Tên sản phẩm",
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        verbose_name="Đường dẫn thân thiện",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Mô tả sản phẩm",
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Giá bán (VNĐ)",
    )

    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Số lượng tồn kho",
    )

    class Gender(models.TextChoices):
        FEMALE = "nu", "Nữ"
        MALE = "nam", "Nam"
        UNISEX = "unisex", "Unisex"

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNISEX,
        verbose_name="Giới tính",
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="Ảnh sản phẩm",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang bày bán",
    )

    sku = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Mã sản phẩm (SKU)",
    )

    specs = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Thông số kỹ thuật",
    )

    care_instructions = models.TextField(
        blank=True,
        verbose_name="Hướng dẫn bảo quản",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật gần nhất")

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        # Thuộc tính tiện ích: cho biết sản phẩm còn hàng hay không, dùng
        # trực tiếp trong template bằng cú pháp {{ product.is_in_stock }}
        # mà không cần gọi như một hàm (không cần dấu ngoặc).
        return self.stock_quantity > 0

    @property
    def description_intro(self):
        # Mô tả sản phẩm được seed dạng: đoạn giới thiệu, rồi tới các dòng
        # bắt đầu bằng "- " liệt kê đặc điểm nổi bật. Thuộc tính này tách ra
        # phần đoạn giới thiệu (mọi dòng KHÔNG bắt đầu bằng "- ") để hiển thị
        # tách biệt với phần bullet trên trang chi tiết sản phẩm.
        lines = [line for line in self.description.splitlines() if line.strip()]
        intro_lines = [line for line in lines if not line.strip().startswith("-")]
        return "\n".join(intro_lines)

    @property
    def description_bullets(self):
        # Phần liệt kê đặc điểm nổi bật: các dòng bắt đầu bằng "- ", bỏ dấu
        # gạch đầu dòng để template chỉ cần bọc lại bằng thẻ <li>.
        lines = [line.strip() for line in self.description.splitlines() if line.strip()]
        return [line.lstrip("-").strip() for line in lines if line.startswith("-")]


class ProductImage(models.Model):
    """
    Ảnh phụ (gallery) của một sản phẩm, bổ sung thêm cho ảnh chính
    (Product.image). Quan hệ Một-Nhiều: một sản phẩm có nhiều ảnh gallery.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Sản phẩm",
    )

    image = models.ImageField(
        upload_to="products/gallery/",
        verbose_name="Ảnh",
    )

    position = models.PositiveIntegerField(
        default=0,
        verbose_name="Thứ tự hiển thị",
    )

    class Meta:
        verbose_name = "Ảnh sản phẩm"
        verbose_name_plural = "Ảnh sản phẩm (gallery)"
        ordering = ["position"]

    def __str__(self):
        return f"Ảnh #{self.position} của {self.product.name}"
