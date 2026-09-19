"""
Form cho app "accounts".

RegisterForm kế thừa UserCreationForm có sẵn của Django (đã xử lý sẵn việc
băm mật khẩu, kiểm tra 2 lần nhập mật khẩu khớp nhau, chạy AUTH_PASSWORD_VALIDATORS
khai báo trong settings.py), chỉ bổ sung thêm các trường thông tin riêng của
model User tùy biến (email, số điện thoại, địa chỉ).
"""

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm

from .models import User

TEXT_INPUT_CLASS = "form-input"


def _apply_input_class(fields):
    for field in fields:
        existing_class = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = f"{existing_class} {TEXT_INPUT_CLASS}".strip()


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


class ForgotPasswordVerifyForm(forms.Form):
    """
    Bước 1 của luồng "Quên mật khẩu". Dự án chưa cấu hình gửi email thật
    (không có SMTP), nên thay vì gửi link reset qua email, xác minh danh
    tính bằng cách đối chiếu username + email/SĐT người dùng tự nhập với
    đúng hồ sơ đã lưu - khớp thì mới cho sang bước đặt mật khẩu mới.

    LƯU Ý bảo mật: cách xác minh này yếu hơn gửi link qua email thật (ai
    biết được username + email/SĐT của người khác cũng reset được mật khẩu
    hộ họ), chấp nhận được cho quy mô đồ án. Luôn trả về CÙNG MỘT thông báo
    lỗi chung dù username không tồn tại hay email/SĐT không khớp, để không
    lộ ra tài khoản nào có tồn tại trong hệ thống (chống dò tài khoản).
    """

    username = forms.CharField(label="Tên đăng nhập")
    contact = forms.CharField(label="Email hoặc số điện thoại đã đăng ký")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_input_class(self.fields.values())

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username", "").strip()
        contact = cleaned.get("contact", "").strip()

        if username and contact:
            user = User.objects.filter(username=username).first()
            matched = user is not None and (
                contact.lower() == user.email.lower()
                or (user.phone_number and contact == user.phone_number)
            )
            if not matched:
                raise forms.ValidationError(
                    "Thông tin không khớp với tài khoản nào. Vui lòng kiểm tra lại "
                    "tên đăng nhập và email/số điện thoại đã đăng ký."
                )
            cleaned["user"] = user

        return cleaned


class SetNewPasswordForm(forms.Form):
    """
    Bước 2 của luồng "Quên mật khẩu": đặt mật khẩu mới cho user đã xác minh
    ở bước 1 (truyền vào qua __init__, không lấy từ form data để tránh bị
    giả mạo đổi mật khẩu user khác).
    """

    new_password1 = forms.CharField(label="Mật khẩu mới", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Nhập lại mật khẩu mới", widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        _apply_input_class(self.fields.values())

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")
        if password:
            # Chạy đúng AUTH_PASSWORD_VALIDATORS đã khai báo trong settings.py
            # (giống lúc đăng ký), không cho đặt mật khẩu quá yếu/quá ngắn.
            password_validation.validate_password(password, self.user)
        return password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Hai lần nhập mật khẩu không khớp nhau.")
        return password2

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save(update_fields=["password"])
        return self.user
