"""
View cho app "cart": thêm/sửa số lượng/xóa sản phẩm trong giỏ hàng, xem tổng
tiền.

GIỎ HÀNG KHÁCH VÃNG LAI: các thao tác trong file này KHÔNG bắt buộc đăng
nhập nữa - khách chưa đăng nhập vẫn có giỏ hàng riêng (gắn với session, xem
_get_cart() bên dưới). Chỉ bước "Đặt hàng" (orders/views.py::checkout) mới
bắt buộc đăng nhập, và khi đăng nhập thành công, giỏ hàng khách vãng lai
được gộp vào giỏ hàng của tài khoản (xem cart/services.py).

AJAX: cart_update/cart_remove trả về JSON khi request gửi kèm header
"X-Requested-With: XMLHttpRequest" (do static/js/main.js tự gắn khi gọi
fetch), để trang giỏ hàng cập nhật số lượng/tổng tiền mà KHÔNG cần tải lại
cả trang. Nếu không có header này (ví dụ JS bị tắt), view vẫn hoạt động
đúng theo kiểu cũ: redirect kèm flash message.
"""

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from products.models import Product

from .models import Cart, CartItem


def _format_money(value):
    # Định dạng số tiền kiểu Việt Nam (dấu chấm ngăn cách hàng nghìn), dùng
    # cho phần trả JSON - template thường dùng filter "intcomma" của Django
    # nhưng filter đó không áp dụng được cho response JSON viết tay ở đây.
    return f"{value:,.0f}".replace(",", ".")


def _get_cart(request, create=True):
    # Nguồn duy nhất xác định "giỏ hàng của request này là giỏ nào":
    #   - Đã đăng nhập -> giỏ hàng gắn với User (luôn có sẵn nhờ signal ở
    #     accounts/signals.py, nhưng vẫn get_or_create phòng tài khoản cũ).
    #   - Chưa đăng nhập -> giỏ hàng gắn với session hiện tại. Phải chủ động
    #     tạo session (request.session.create()) nếu đây là request ĐẦU
    #     TIÊN của trình duyệt này, vì Django chỉ thật sự lưu session (và
    #     có session_key) sau khi có ít nhất một lần ghi dữ liệu vào đó.
    if request.user.is_authenticated:
        if create:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            return cart
        return Cart.objects.filter(user=request.user).first()

    if not request.session.session_key:
        if not create:
            return None
        request.session.create()

    session_key = request.session.session_key
    if create:
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
        return cart
    return Cart.objects.filter(session_key=session_key, user=None).first()


@never_cache  # tránh trình duyệt hiện lại giỏ hàng cũ qua back-forward cache (xem orders/views.py::my_orders)
def cart_view(request):
    cart = _get_cart(request, create=False)
    items = cart.items.select_related("product", "product__category").all() if cart else []
    context = {
        "cart": cart,
        "items": items,
    }
    return render(request, "cart/cart.html", context)


@require_POST
def cart_add(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, is_active=True)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 1
    quantity = max(1, quantity)

    if not product.is_in_stock:
        messages.error(request, f"\"{product.name}\" hiện đã hết hàng.")
        return redirect("products:detail", slug=product.slug)

    cart = _get_cart(request)
    cart.add_product(product, quantity=quantity)
    messages.success(request, f"Đã thêm \"{product.name}\" vào giỏ hàng.")
    return redirect("cart:view")


@require_POST
def cart_update(request, item_id):
    cart = _get_cart(request, create=False)
    if cart is None:
        raise Http404("Giỏ hàng không tồn tại.")
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    try:
        quantity = int(request.POST.get("quantity", item.quantity))
    except ValueError:
        quantity = item.quantity

    max_quantity = item.product.stock_quantity or 1
    quantity = max(1, min(quantity, max_quantity))
    item.quantity = quantity
    item.save(update_fields=["quantity"])

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        return JsonResponse({
            "ok": True,
            "removed": False,
            "item_id": item.id,
            "item_quantity": item.quantity,
            "item_line_total": _format_money(item.line_total),
            "cart_total_items": cart.total_items,
            "cart_total_price": _format_money(cart.total_price),
        })

    messages.success(request, f"Đã cập nhật số lượng \"{item.product.name}\".")
    return redirect("cart:view")


@require_POST
def cart_remove(request, item_id):
    cart = _get_cart(request, create=False)
    if cart is None:
        raise Http404("Giỏ hàng không tồn tại.")
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    product_name = item.product.name
    item.delete()

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        return JsonResponse({
            "ok": True,
            "removed": True,
            "item_id": item_id,
            "cart_total_items": cart.total_items,
            "cart_total_price": _format_money(cart.total_price),
        })

    messages.success(request, f"Đã xóa \"{product_name}\" khỏi giỏ hàng.")
    return redirect("cart:view")
