from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Cấu hình cho app "orders": đơn hàng đã đặt (bằng chứng đã mua).
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = "Đơn hàng"
