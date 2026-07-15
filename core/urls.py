"""
URL configuration for core project.

File này là "trạm trung chuyển" của toàn bộ dự án: nó không tự định nghĩa
trang web nào cả, mà chỉ include() các file urls.py con nằm bên trong từng
app (accounts, products, wishlist, wallet). Khi có app mới, ta chỉ cần thêm
một dòng path(..., include(...)) tại đây.

LƯU Ý: Ở giai đoạn hiện tại (mới thiết kế Model + kết nối MySQL), các app
accounts/products/wishlist/wallet CHƯA có file urls.py và views.py, nên
phần include() dưới đây đang được chú thích lại. Ở bước tiếp theo (khi viết
Views và Template), ta sẽ bỏ chú thích các dòng này ra.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('gio-hang/', include('cart.urls')),
    # path('wishlist/', include('wishlist.urls')),
    # path('wallet/', include('wallet.urls')),
    path('', include('products.urls')),
]

# Chỉ phục vụ file media (ảnh sản phẩm do người dùng upload) theo cách này
# khi đang chạy ở môi trường phát triển (DEBUG=True). Khi triển khai thật,
# việc phục vụ file media phải do Nginx/Apache đảm nhiệm, không dùng Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
