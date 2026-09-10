from django.apps import AppConfig


class FavoritesConfig(AppConfig):
    """
    Cấu hình cho app "favorites".
    App này chịu trách nhiệm về: danh sách sản phẩm yêu thích của từng
    người dùng (quan hệ Many-to-Many giữa User và Product).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "favorites"
    verbose_name = "Danh sách yêu thích"
