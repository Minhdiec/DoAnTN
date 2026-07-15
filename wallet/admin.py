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


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type", "amount", "balance_after", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("wallet__user__username",)
