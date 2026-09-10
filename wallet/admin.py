from django.contrib import admin

from .models import Transaction, Wallet


class TransactionInline(admin.TabularInline):
    # Inline giúp hiển thị luôn danh sách giao dịch ngay bên trong trang
    # chi tiết của một Wallet, không cần chuyển sang màn hình khác để xem.
    model = Transaction
    extra = 0
    readonly_fields = ("transaction_type", "amount", "balance_after", "description", "created_at")
    can_delete = False
    ordering = ("-created_at",)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__username",)
    inlines = [TransactionInline]

    def has_add_permission(self, request):
        # Wallet được TỰ ĐỘNG tạo qua signal ngay khi có User mới (1-1 với
        # User, xem accounts/signals.py) - admin tự thêm 1 Wallet ở đây vừa
        # thừa (user nào cũng đã có sẵn) vừa dễ tạo ví "mồ côi" không gắn
        # đúng user nào cần dùng tới.
        return False

    def has_change_permission(self, request, obj=None):
        # Số dư CHỈ được đổi qua Wallet.deposit()/withdraw() (luôn tạo kèm 1
        # Transaction tương ứng để đối soát) - cho admin sửa thẳng "balance"
        # ở đây sẽ tạo ra số dư không khớp với lịch sử giao dịch bên dưới.
        return False


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type", "amount", "balance_after", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("wallet__user__username",)

    def has_add_permission(self, request):
        # Transaction chỉ được tạo bên trong Wallet.deposit()/withdraw() -
        # admin tự thêm 1 dòng ở đây sẽ có "balance_after" bịa tay, không
        # khớp số dư thật của ví (phá vỡ mục đích đối soát của bảng này).
        return False

    def has_change_permission(self, request, obj=None):
        # Lịch sử giao dịch phải BẤT BIẾN để còn đối soát được - sửa lại số
        # tiền/số dư sau giao dịch của 1 dòng cũ sẽ làm sai lệch toàn bộ
        # chuỗi đối soát các dòng sau nó.
        return False
