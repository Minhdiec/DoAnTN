"""
URL configuration for core project.

File này là "trạm trung chuyển" của toàn bộ dự án: nó không tự định nghĩa
trang web nào cả, mà chỉ include() các file urls.py con nằm bên trong từng
app (accounts, products, favorites, wallet). Khi có app mới, ta chỉ cần thêm
một dòng path(..., include(...)) tại đây.

LƯU Ý: Ở giai đoạn hiện tại (mới thiết kế Model + kết nối MySQL), các app
accounts/products/favorites/wallet CHƯA có file urls.py và views.py, nên
phần include() dưới đây đang được chú thích lại. Ở bước tiếp theo (khi viết
Views và Template), ta sẽ bỏ chú thích các dòng này ra.
"""
import types

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.urls import include, path

# Đổi tên thương hiệu hiển thị ở trang quản trị (title tab, dòng chữ trên
# đầu trang, tiêu đề trang chủ /admin/) - đồng bộ với tên site "Astraea"
# (xem templates/admin/base_site.html cho phần đổi màu giao diện).
admin.site.site_header = "Astraea - Quản trị"
admin.site.site_title = "Astraea Admin"
admin.site.index_title = "Trang quản trị hệ thống"


def _get_app_list_with_orders_first(self, request, app_label=None):
    # Mặc định Django xếp các mục trên trang chủ /admin (và thanh điều
    # hướng bên trái) theo THỨ TỰ BẢNG CHỮ CÁI của tên app, không theo mức
    # độ quan trọng. "Đơn hàng" là mục admin thao tác nhiều nhất (theo dõi
    # + cập nhật trạng thái giao hàng) nên đưa lên đầu danh sách cho dễ
    # thấy, các mục còn lại vẫn giữ nguyên thứ tự bảng chữ cái phía sau.
    app_list = AdminSite.get_app_list(self, request, app_label=app_label)
    app_list.sort(key=lambda app: app["app_label"] != "orders")
    return app_list


admin.site.get_app_list = types.MethodType(_get_app_list_with_orders_first, admin.site)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('gio-hang/', include('cart.urls')),
    path('don-hang/', include('orders.urls')),
    path('danh-gia/', include('reviews.urls')),
    path('yeu-thich/', include('favorites.urls')),
    # path('wallet/', include('wallet.urls')),
    path('', include('products.urls')),
]

# Chỉ phục vụ file media (ảnh sản phẩm do người dùng upload) theo cách này
# khi đang chạy ở môi trường phát triển (DEBUG=True). Khi triển khai thật,
# việc phục vụ file media phải do Nginx/Apache đảm nhiệm, không dùng Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
