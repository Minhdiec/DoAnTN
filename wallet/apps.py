from django.apps import AppConfig


class WalletConfig(AppConfig):
    """
    Cấu hình cho app "wallet".
    App này chịu trách nhiệm về: ví điện tử của người dùng (số dư), nạp
    tiền mô phỏng, trừ tiền khi thanh toán và lịch sử giao dịch.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "wallet"
    verbose_name = "Ví điện tử"
