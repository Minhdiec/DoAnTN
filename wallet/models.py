"""
Model cho app "wallet".

Đây là phần quan trọng nhất về mặt xử lý số liệu của toàn bộ dự án: Ví
điện tử. Mọi phép tính liên quan tới tiền (số dư, số tiền nạp, số tiền
trừ...) đều BẮT BUỘC dùng kiểu Decimal của Python (từ thư viện chuẩn
"decimal"), thay vì kiểu float thông thường.

Lý do: kiểu float lưu số theo hệ nhị phân nên không thể biểu diễn chính
xác tuyệt đối các số thập phân trong hệ thập phân (ví dụ 0.1 không có
biểu diễn nhị phân hữu hạn), dẫn tới sai số cộng dồn sau nhiều phép tính.
Với một hệ thống tài chính như ví điện tử, chỉ một sai số rất nhỏ cũng có
thể gây lệch số dư sau hàng nghìn giao dịch. Kiểu Decimal lưu số thập phân
đúng như con người viết ra, nên phép cộng/trừ tiền luôn chính xác tuyệt đối.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction


class Wallet(models.Model):
    """
    Ví điện tử của một người dùng. Mỗi User có đúng một Wallet
    (quan hệ OneToOneField - Một-Một).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
        verbose_name="Người dùng",
        help_text="Mỗi người dùng chỉ có đúng một ví điện tử.",
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Số dư (VNĐ)",
        help_text="Số dư hiện tại trong ví, luôn được đảm bảo lớn hơn hoặc bằng 0.",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo ví")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Lần cập nhật gần nhất")

    class Meta:
        verbose_name = "Ví điện tử"
        verbose_name_plural = "Ví điện tử"

    def __str__(self):
        return f"Ví của {self.user.username} - Số dư: {self.balance:,} VNĐ"

    def deposit(self, amount, description="Nạp tiền vào ví"):
        """
        Nạp tiền vào ví (mô phỏng, không kết nối cổng thanh toán thật).

        Tham số "amount" phải là kiểu Decimal và phải lớn hơn 0.
        Hàm này tạo đồng thời một bản ghi Transaction để lưu lại lịch sử
        giao dịch, giúp người dùng xem lại được mọi lần nạp/trừ tiền.
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        if amount <= Decimal("0.00"):
            raise ValueError("Số tiền nạp phải lớn hơn 0.")

        # transaction.atomic() đảm bảo toàn bộ khối lệnh bên trong hoặc là
        # thực hiện thành công TOÀN BỘ, hoặc là không có gì thay đổi cả nếu
        # có lỗi xảy ra giữa chừng (ví dụ mất kết nối MySQL). Điều này giúp
        # số dư ví và lịch sử giao dịch luôn đồng bộ với nhau.
        with transaction.atomic():
            # select_for_update() khóa dòng dữ liệu ví này lại trong lúc xử
            # lý, tránh trường hợp hai request nạp tiền/trừ tiền chạy đồng
            # thời làm sai lệch số dư (race condition).
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            wallet.balance = wallet.balance + amount
            wallet.save(update_fields=["balance", "updated_at"])

            Transaction.objects.create(
                wallet=wallet,
                transaction_type=Transaction.TransactionType.DEPOSIT,
                amount=amount,
                balance_after=wallet.balance,
                description=description,
            )

            self.balance = wallet.balance

        return self.balance

    def withdraw(self, amount, description="Thanh toán đơn hàng"):
        """
        Trừ tiền trong ví, dùng khi người dùng thanh toán đơn hàng.

        Nếu số dư hiện tại không đủ để trừ, hàm sẽ ném ra lỗi ValueError
        và KHÔNG có bất kỳ thay đổi nào được lưu vào database.
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        if amount <= Decimal("0.00"):
            raise ValueError("Số tiền thanh toán phải lớn hơn 0.")

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)

            if wallet.balance < amount:
                raise ValueError("Số dư trong ví không đủ để thực hiện giao dịch này.")

            wallet.balance = wallet.balance - amount
            wallet.save(update_fields=["balance", "updated_at"])

            Transaction.objects.create(
                wallet=wallet,
                transaction_type=Transaction.TransactionType.PAYMENT,
                amount=amount,
                balance_after=wallet.balance,
                description=description,
            )

            self.balance = wallet.balance

        return self.balance


class Transaction(models.Model):
    """
    Lịch sử một giao dịch (nạp tiền hoặc thanh toán) của ví điện tử.

    Mỗi lần số dư ví thay đổi, hệ thống bắt buộc phải tạo ra một bản ghi
    Transaction tương ứng để đảm bảo có thể tra soát lại được sau này -
    đây là nguyên tắc bắt buộc trong mọi hệ thống liên quan đến tài chính.
    """

    class TransactionType(models.TextChoices):
        # models.TextChoices giúp ta định nghĩa các lựa chọn cố định (giống
        # như enum) một cách tường minh, tránh viết nhầm chuỗi ký tự tự do.
        DEPOSIT = "DEPOSIT", "Nạp tiền"
        PAYMENT = "PAYMENT", "Thanh toán"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Ví điện tử",
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        verbose_name="Loại giao dịch",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Số tiền giao dịch (VNĐ)",
        help_text="Luôn là số dương, chiều tăng/giảm số dư được xác định bởi transaction_type.",
    )

    balance_after = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Số dư sau giao dịch (VNĐ)",
        help_text="Số dư của ví ngay SAU KHI giao dịch này hoàn tất, dùng để tra soát đối chiếu.",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian giao dịch")

    class Meta:
        verbose_name = "Giao dịch ví điện tử"
        verbose_name_plural = "Lịch sử giao dịch ví điện tử"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount:,} VNĐ"
