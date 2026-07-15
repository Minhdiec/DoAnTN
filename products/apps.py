from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """
    Cấu hình cho app "products".
    App này chịu trách nhiệm về: danh mục sản phẩm (Category), sản phẩm
    (Product) và toàn bộ chức năng CRUD (thêm/sửa/xóa/xem) sản phẩm.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "products"
    verbose_name = "Sản phẩm"
