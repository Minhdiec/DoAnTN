from django.apps import AppConfig


class CartConfig(AppConfig):
    """
    Cấu hình cho app "cart": giỏ hàng của từng người dùng.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cart'
    verbose_name = "Giỏ hàng"
