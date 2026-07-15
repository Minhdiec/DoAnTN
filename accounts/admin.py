from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Đăng ký model User tùy biến vào trang quản trị /admin.
    Kế thừa UserAdmin có sẵn của Django để vẫn giữ được đầy đủ tính năng
    quản lý mật khẩu, phân quyền mặc định, đồng thời hiển thị thêm các cột
    thông tin riêng mà ta vừa thêm vào (số điện thoại, địa chỉ).
    """

    fieldsets = UserAdmin.fieldsets + (
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

    search_fields = ("username", "email", "phone_number")
