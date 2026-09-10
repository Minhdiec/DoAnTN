"""
Context processor: bơm số lượng sản phẩm trong giỏ hàng vào MỌI template,
để badge trên icon giỏ hàng ở header (templates/base.html) luôn hiển thị
đúng số lượng dù đang ở trang nào, không phải khai báo lại trong từng view.
"""

from .models import Cart


def cart_summary(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        # Khách vãng lai: đọc giỏ hàng gắn với session hiện tại (nếu session
        # này đã từng ghi gì đó, tức là đã từng thêm sản phẩm - xem
        # cart/views.py::_get_cart). Chưa có session_key nghĩa là chắc chắn
        # chưa thêm gì, khỏi cần truy vấn.
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key, user=None).first() if session_key else None

    return {"cart_item_count": cart.total_items if cart else 0}
