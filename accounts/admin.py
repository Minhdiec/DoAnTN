from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import User

# Model "Nhóm" (Group) của Django dùng để phân quyền theo nhóm - đồ án này
# chỉ phân quyền đơn giản qua is_staff/is_superuser (xem accounts/views.py,
# reviews template), không dùng Group ở bất kỳ đâu, nên bỏ khỏi trang admin
# cho gọn thay vì để 1 mục trống không ai dùng tới.
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Đăng ký model User tùy biến vào trang quản trị /admin.
    Kế thừa UserAdmin có sẵn của Django để vẫn giữ được đầy đủ tính năng
    phân quyền mặc định, đồng thời hiển thị thêm các cột thông tin riêng mà
    ta vừa thêm vào (số điện thoại, địa chỉ).

    Bỏ trường "password" khỏi fieldsets (khác với UserAdmin gốc): mặc định
    Django hiển thị ở đây bảng chi tiết thuật toán băm/salt/hash của mật
    khẩu - thông tin kỹ thuật không cần thiết cho người quản trị, chỉ nên
    gây rối mắt trang chỉnh sửa người dùng. Bỏ "groups" vì đồ án chỉ phân
    quyền qua is_staff/is_superuser, không dùng model Group (xem
    admin.site.unregister(Group) ở trên).
    """

    fieldsets = (
        (None, {"fields": ("username",)}),
        ("Thông tin cá nhân", {"fields": ("first_name", "last_name", "email")}),
        (
            "Phân quyền",
            {"fields": ("is_active", "is_staff", "is_superuser", "user_permissions")},
        ),
        ("Ngày quan trọng", {"fields": ("last_login", "date_joined")}),
        ("Thông tin bổ sung", {"fields": ("phone_number", "address", "avatar")}),
    )

    list_display = (
        "username",
        "email",
        "phone_number",
        "is_staff",
        "is_active",
        "created_at",
    )

    list_filter = ("is_staff", "is_superuser", "is_active")
    filter_horizontal = ("user_permissions",)
    search_fields = ("username", "email", "phone_number")
