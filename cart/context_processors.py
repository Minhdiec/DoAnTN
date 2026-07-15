"""
Context processor: bơm số lượng sản phẩm trong giỏ hàng vào MỌI template,
để badge trên icon giỏ hàng ở header (templates/base.html) luôn hiển thị
đúng số lượng dù đang ở trang nào, không phải khai báo lại trong từng view.
"""

from .models import Cart


def cart_summary(request):
    if not request.user.is_authenticated:
        return {"cart_item_count": 0}

    cart = Cart.objects.filter(user=request.user).first()
    return {"cart_item_count": cart.total_items if cart else 0}
