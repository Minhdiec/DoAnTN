from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Cấu hình cho app "accounts".
    App này chịu trách nhiệm về: model User tùy biến, đăng ký, đăng nhập,
    đăng xuất và trang thông tin cá nhân của người dùng.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Tài khoản người dùng"

    def ready(self):
        # Import signals ở đây (không import ở đầu file models.py/apps.py)
        # để đảm bảo Django đã nạp xong toàn bộ app registry trước khi
        # signals.py import model từ các app khác (cart, wallet, favorites).
        from . import signals  # noqa: F401
