from django.apps import AppConfig


class WishlistConfig(AppConfig):
    """
    Cấu hình cho app "wishlist".
    App này chịu trách nhiệm về: danh sách sản phẩm yêu thích của từng
    người dùng (quan hệ Many-to-Many giữa User và Product).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "wishlist"
    verbose_name = "Danh sách yêu thích"
