from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    # Inline giúp xem luôn danh sách sản phẩm của một đơn hàng ngay trong
    # trang chi tiết Order, không cần chuyển sang màn hình khác.
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "payment_method",
        "total_amount",
        "created_at",
        "xem_chi_tiet",
    )
    list_filter = ("status", "payment_method")
    search_fields = ("user__username", "shipping_address", "recipient_phone")
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        # Đơn hàng CHỈ được tạo qua orders/views.py::checkout() (đi kèm trừ
        # tồn kho + xóa giỏ hàng đúng luồng) - admin tự tạo 1 đơn từ đây sẽ
        # không có sản phẩm/tồn kho đi kèm, dữ liệu sai lệch ngay từ đầu.
        return False

    def has_change_permission(self, request, obj=None):
        # Đơn hàng là dữ liệu LỊCH SỬ (khách đã mua gì, giá bao nhiêu, giao
        # đến đâu) - admin sửa lại các trường này sẽ làm sai lệch bằng chứng
        # đã mua mà app reviews dựa vào. Vẫn xem được chi tiết (chỉ đọc).
        return False

    @admin.display(description="")
    def xem_chi_tiet(self, obj):
        url = reverse("admin:orders_order_change", args=[obj.pk])
        return format_html('<a href="{}">Chi tiết đơn hàng →</a>', url)
