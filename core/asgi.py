"""
ASGI config cho dự án core.

Khác với file wsgi.py (chỉ xử lý được HTTP thông thường: 1 request -> 1
response rồi đóng kết nối), file này định tuyến CẢ HTTP LẪN WEBSOCKET
(giao thức giữ kết nối liên tục, cho phép server chủ động gửi dữ liệu về
client bất cứ lúc nào) - bắt buộc phải có WebSocket để module thử kính ảo
truyền khung hình webcam qua lại real-time (xem CLAUDE_PROGRESS.md mục 2,
quyết định #2: KHÔNG dùng HTTP polling lặp lại mỗi khung hình).

ProtocolTypeRouter hoạt động như một "trạm phân loại" ở tầng ngoài cùng:
nhìn vào GIAO THỨC của kết nối đến (http hay websocket) rồi chuyển tiếp cho
đúng bộ xử lý tương ứng - HTTP vẫn đi qua get_asgi_application() y hệt từ
trước (không đổi hành vi các app cũ), WebSocket đi qua URLRouter riêng của
app "tryon" (xem tryon/routing.py).
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Phải gọi get_asgi_application() TRƯỚC khi import bất kỳ module nào có
# đụng tới model Django (kể cả gián tiếp qua tryon.routing) - đây là yêu cầu
# thứ tự nạp bắt buộc của Django (app registry phải sẵn sàng trước), nếu
# import ngược lại sẽ báo lỗi "Apps aren't loaded yet".
django_asgi_app = get_asgi_application()

from tryon.routing import websocket_urlpatterns  # noqa: E402  (xem lý do ở trên)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})
