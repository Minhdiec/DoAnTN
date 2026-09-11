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
        "delivery_status",
        "payment_method",
        "shipping_carrier",
        "total_amount",
        "created_at",
        "xem_chi_tiet",
    )
    list_filter = ("status", "delivery_status", "payment_method", "shipping_carrier")
    search_fields = ("user__username", "shipping_address", "recipient_phone")
    inlines = [OrderItemInline]

    # Đơn hàng là dữ liệu LỊCH SỬ (khách đã mua gì, giá bao nhiêu, giao đến
    # đâu) - admin sửa lại các trường này sẽ làm sai lệch bằng chứng đã mua
    # mà app reviews dựa vào, nên toàn bộ ở đây chỉ đọc. Riêng
    # "delivery_status" được PHÉP sửa vì đó là tiến trình giao hàng thật sự
    # thay đổi theo thời gian (đơn vị vận chuyển báo về), không phải bằng
    # chứng đã mua.
    readonly_fields = (
        "user",
        "status",
        "total_amount",
        "payment_method",
        "shipping_carrier",
        "recipient_name",
        "shipping_address",
        "recipient_phone",
        "created_at",
    )

    def has_add_permission(self, request):
        # Đơn hàng CHỈ được tạo qua orders/views.py::checkout() (đi kèm trừ
        # tồn kho + xóa giỏ hàng đúng luồng) - admin tự tạo 1 đơn từ đây sẽ
        # không có sản phẩm/tồn kho đi kèm, dữ liệu sai lệch ngay từ đầu.
        return False

    @admin.display(description="")
    def xem_chi_tiet(self, obj):
        url = reverse("admin:orders_order_change", args=[obj.pk])
        return format_html('<a href="{}">Chi tiết đơn hàng →</a>', url)
