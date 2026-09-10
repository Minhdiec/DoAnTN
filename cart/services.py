"""
Hàm tiện ích dùng chung liên quan tới giỏ hàng, tách riêng khỏi views.py vì
được gọi từ app khác (accounts/views.py, lúc đăng nhập/đăng ký thành công).
"""

from .models import Cart


def merge_guest_cart_into_user(session_key, user):
    # Sau khi đăng nhập/đăng ký thành công, nếu trình duyệt này TRƯỚC ĐÓ đã
    # có giỏ hàng khách vãng lai (gắn với session_key), gộp toàn bộ sản phẩm
    # trong đó vào giỏ hàng thật của tài khoản rồi xóa giỏ khách vãng lai đi -
    # tránh mất sản phẩm khách đã chọn trước khi đăng nhập.
    #
    # QUAN TRỌNG: "session_key" phải được lấy TRƯỚC khi gọi django.contrib.
    # auth.login() - Django tự XOAY VÒNG (rotate) session key mỗi lần login
    # thành công (chống tấn công session fixation), nên nếu đọc
    # request.session.session_key SAU login() sẽ luôn ra khóa MỚI, không
    # bao giờ khớp với giỏ hàng khách vãng lai đã tạo trước đó.
    if not session_key:
        return

    guest_cart = Cart.objects.filter(session_key=session_key, user=None).first()
    if guest_cart is None:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    user_cart.merge_from(guest_cart)
