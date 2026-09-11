"""
Model cho app "accounts".

Ở đây ta định nghĩa model User TÙY BIẾN (custom User model) thay vì dùng
thẳng User mặc định của Django. Đây là thực hành chuẩn (best practice) khi
bắt đầu một dự án Django mới: ngay từ đầu, ta kế thừa AbstractUser để sau
này có thể thoải mái thêm các trường thông tin riêng (số điện thoại, địa
chỉ, ảnh đại diện...) mà không phải viết một bảng phụ rồi nối (join) tốn
kém về sau.

Model User này sẽ tự động có sẵn các trường cơ bản do AbstractUser cung
cấp: username, password, email, first_name, last_name, is_active,
is_staff, is_superuser, date_joined, last_login...
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    User tùy biến, kế thừa toàn bộ chức năng xác thực (đăng nhập, mã hóa
    mật khẩu, phân quyền...) của Django, đồng thời bổ sung thêm các trường
    thông tin cần thiết cho một website thương mại điện tử.
    """

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="Số điện thoại",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Địa chỉ",
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Ảnh đại diện",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo tài khoản",
    )

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"

    def __str__(self):
        # Hàm này quyết định User sẽ hiển thị như thế nào khi in ra hoặc
        # hiển thị trong trang quản trị (Django admin). Ưu tiên hiển thị
        # username vì đó là trường luôn có giá trị và luôn duy nhất.
        return self.username
