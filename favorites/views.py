"""
View cho app "favorites": bật/tắt yêu thích 1 sản phẩm và xem lại danh sách
sản phẩm đã yêu thích.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import Product

from .models import Favorite


@login_required
def list_view(request):
    favorite, _ = Favorite.objects.get_or_create(user=request.user)
    products = favorite.products.filter(is_active=True).select_related("category")
    context = {
        "products": products,
        # Mọi sản phẩm ở đây đều đã yêu thích - dùng lại đúng biến này để
        # products/_favorite_button.html (include chung) tô đậm được trái
        # tim, không cần viết logic riêng cho trang này.
        "favorite_product_ids": set(products.values_list("id", flat=True)),
    }
    return render(request, "favorites/list.html", context)


@require_POST
@login_required
def toggle(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    favorite, _ = Favorite.objects.get_or_create(user=request.user)

    if favorite.has_product(product):
        favorite.remove_product(product)
        messages.success(request, f"Đã bỏ \"{product.name}\" khỏi danh sách yêu thích.")
    else:
        favorite.add_product(product)
        messages.success(request, f"Đã thêm \"{product.name}\" vào danh sách yêu thích.")

    # "next" luôn do chính template của ta điền (giá trị request.path của
    # trang đang đứng), không phải tham số người dùng tự do nhập - nên an
    # toàn để redirect thẳng, không lo bị lợi dụng làm open-redirect.
    next_url = request.POST.get("next") or "products:home"
    return redirect(next_url)
