"""
Form cho app "accounts".

RegisterForm kế thừa UserCreationForm có sẵn của Django (đã xử lý sẵn việc
băm mật khẩu, kiểm tra 2 lần nhập mật khẩu khớp nhau, chạy AUTH_PASSWORD_VALIDATORS
khai báo trong settings.py), chỉ bổ sung thêm các trường thông tin riêng của
model User tùy biến (email, số điện thoại, địa chỉ).
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User

TEXT_INPUT_CLASS = "form-input"


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "phone_number", "address"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["phone_number"].required = False
        self.fields["address"].required = False

        # UserCreationForm tự sinh thêm 2 trường password1/password2, ta gắn
        # class CSS cho TẤT CẢ các trường (kể cả 2 trường mật khẩu này) trong
        # một vòng lặp duy nhất thay vì khai báo widget riêng cho từng trường.
        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} {TEXT_INPUT_CLASS}".strip()


class ProfileForm(forms.ModelForm):
    """
    Form chỉnh sửa hồ sơ cá nhân: họ tên, email, số điện thoại, địa chỉ nhận
    hàng mặc định, ảnh đại diện. KHÔNG cho đổi username/mật khẩu ở đây (đổi
    mật khẩu là một luồng riêng, có xác thực mật khẩu cũ - ngoài phạm vi
    trang hồ sơ đơn giản này).
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "address", "avatar"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

        for name, field in self.fields.items():
            if name == "avatar":
                continue
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} {TEXT_INPUT_CLASS}".strip()
