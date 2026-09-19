"""
View cho app "orders": đặt hàng từ giỏ hàng và xem lại danh sách đơn hàng đã
đặt ("Đơn hàng của tôi").

LƯU Ý: bước thanh toán hiện đang GIẢ LẬP (theo yêu cầu người dùng - xem
BUG.ipynb) vì đồ án chưa nối cổng thanh toán thật (MoMo/thẻ) và người dùng
thường cũng chưa có cách nạp tiền vào Ví điện tử. Người mua chỉ cần CHỌN một
hình thức thanh toán (COD/MoMo/Thẻ) ở modal trên trang giỏ hàng là đơn được
coi là thanh toán thành công ngay, KHÔNG kiểm tra/trừ số dư ví.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from cart.models import Cart
from reviews.models import Review

from .models import Order, OrderItem


@login_required
# @never_cache: không có decorator này, trình duyệt (đặc biệt cơ chế
# back-forward cache khi bấm nút Back) có thể hiện lại "ảnh chụp" trang này
# từ lần tải trước đó thay vì tải lại danh sách đơn mới nhất - user báo
# "vào trang không thấy đơn cũ, đặt đơn mới xong mới thấy" chính là do
# trang trước đó được cache lại lúc chưa có đủ đơn.
@never_cache
def my_orders(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )
    # Sản phẩm nào user này đã đánh giá rồi - dùng để quyết định có hiện nút
    # "Đánh giá" cho từng dòng sản phẩm trong đơn hay không (mỗi sản phẩm đã
    # mua chỉ đánh giá được 1 lần, xem reviews/models.py).
    reviewed_product_ids = set(
        Review.objects.filter(user=request.user).values_list("product_id", flat=True)
    )
    context = {"orders": orders, "reviewed_product_ids": reviewed_product_ids}
    return render(request, "orders/my_orders.html", context)


@require_POST
@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related("product"))

    if not items:
        messages.error(request, "Giỏ hàng đang trống, không thể đặt hàng.")
        return redirect("cart:view")

    for item in items:
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f"\"{item.product.name}\" không còn đủ hàng trong kho.")
            return redirect("cart:view")

    payment_method = request.POST.get("payment_method")
    if payment_method not in Order.PaymentMethod.values:
        messages.error(request, "Vui lòng chọn một hình thức thanh toán.")
        return redirect("cart:view")

    shipping_carrier = request.POST.get("shipping_carrier")
    if shipping_carrier not in Order.ShippingCarrier.values:
        messages.error(request, "Vui lòng chọn một đơn vị vận chuyển.")
        return redirect("cart:view")

    # Bắt buộc có tên người nhận + địa chỉ nhận hàng + SĐT người nhận TRƯỚC
    # KHI cho thanh toán (kiểm tra phía server, không chỉ dựa vào thuộc tính
    # "required" của ô nhập - người dùng có thể tắt JS/sửa HTML để bỏ qua).
    recipient_name = request.POST.get("recipient_name", "").strip()
    shipping_address = request.POST.get("shipping_address", "").strip()
    recipient_phone = request.POST.get("recipient_phone", "").strip()
    if not recipient_name or not shipping_address or not recipient_phone:
        messages.error(request, "Vui lòng nhập đầy đủ tên người nhận, địa chỉ nhận hàng và số điện thoại người nhận.")
        return redirect("cart:view")

    total_amount = cart.total_price

    # transaction.atomic() đảm bảo tạo đơn hàng + trừ tồn kho + xóa giỏ hàng
    # thành công TOÀN BỘ hoặc không có gì thay đổi.
    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            payment_method=payment_method,
            shipping_carrier=shipping_carrier,
            recipient_name=recipient_name,
            shipping_address=shipping_address,
            recipient_phone=recipient_phone,
        )
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.price,
            )
            item.product.stock_quantity -= item.quantity
            item.product.save(update_fields=["stock_quantity"])

        cart.items.all().delete()

    messages.success(
        request,
        f"Thanh toán thành công qua {order.get_payment_method_display()}! "
        f"Đơn hàng #{order.pk} đã được giao.",
    )
    return redirect("orders:my_orders")


@require_POST
@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    if order.status == Order.Status.CANCELLED:
        messages.error(request, f"Đơn hàng #{order.pk} đã được hủy từ trước.")
        return redirect("orders:my_orders")

    # transaction.atomic() đảm bảo đổi trạng thái đơn + hoàn tồn kho cho
    # TỪNG sản phẩm trong đơn xảy ra toàn bộ hoặc không có gì thay đổi -
    # tránh trường hợp đơn đã bị đánh dấu hủy nhưng tồn kho hoàn lại nửa
    # chừng nếu có lỗi giữa chừng.
    with transaction.atomic():
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
        for item in order.items.select_related("product"):
            item.product.stock_quantity += item.quantity
            item.product.save(update_fields=["stock_quantity"])

    messages.success(
        request,
        f"Đã hủy đơn hàng #{order.pk}, số lượng tồn kho của các sản phẩm đã được hoàn lại.",
    )
    return redirect("orders:my_orders")
