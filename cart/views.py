"""
View cho app "cart": thêm/sửa số lượng/xóa sản phẩm trong giỏ hàng, xem tổng
tiền. Tất cả đều yêu cầu đăng nhập (giỏ hàng gắn với User trong DB, không
dùng session, nên phải biết đang thao tác trên giỏ của ai).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import Product

from .models import Cart, CartItem


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("product", "product__category").all()
    context = {
        "cart": cart,
        "items": items,
    }
    return render(request, "cart/cart.html", context)


@require_POST
@login_required
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

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.add_product(product, quantity=quantity)
    messages.success(request, f"Đã thêm \"{product.name}\" vào giỏ hàng.")
    return redirect("cart:view")


@require_POST
@login_required
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)

    try:
        quantity = int(request.POST.get("quantity", item.quantity))
    except ValueError:
        quantity = item.quantity

    max_quantity = item.product.stock_quantity or 1
    quantity = max(1, min(quantity, max_quantity))
    item.quantity = quantity
    item.save(update_fields=["quantity"])
    messages.success(request, f"Đã cập nhật số lượng \"{item.product.name}\".")
    return redirect("cart:view")


@require_POST
@login_required
def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    product_name = item.product.name
    item.delete()
    messages.success(request, f"Đã xóa \"{product_name}\" khỏi giỏ hàng.")
    return redirect("cart:view")
