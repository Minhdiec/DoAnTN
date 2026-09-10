"""
Context processor: bơm số lượng sản phẩm yêu thích vào MỌI template, để
badge trên icon "Yêu thích" ở header (templates/base.html) luôn hiển thị
đúng số lượng dù đang ở trang nào - giống hệt cart_summary của app "cart".
"""

from .models import Favorite


def favorites_summary(request):
    if not request.user.is_authenticated:
        return {"favorite_count": 0}

    favorite = Favorite.objects.filter(user=request.user).first()
    return {"favorite_count": favorite.products.count() if favorite else 0}
