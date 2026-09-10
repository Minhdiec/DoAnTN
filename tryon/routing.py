"""
Dinh tuyen WebSocket rieng cho app "tryon" - duoc core/asgi.py import vao
ProtocolTypeRouter.

BUOC B (CLAUDE_PROGRESS.md muc 24): 1 route duy nhat "ws/tryon/" tro toi
TryOnConsumer (tryon/consumers.py). KHONG can id san pham/mau kinh tren
chinh URL - client tu gui lenh "select_glasses" qua tin nhan dau tien sau
khi ket noi (xem docstring tryon/consumers.py) de chon dung mau kinh cua
san pham dang xem, nho vay 1 route duy nhat dung duoc cho moi trang san
pham thay vi phai tao route rieng cho tung san pham.
"""

from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/tryon/", consumers.TryOnConsumer.as_asgi()),
]
