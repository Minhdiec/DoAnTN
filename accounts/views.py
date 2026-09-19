import time

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render

from cart.services import merge_guest_cart_into_user

from .forms import ForgotPasswordVerifyForm, ProfileForm, RegisterForm, SetNewPasswordForm
from .models import User

# Khoá session tạm giữ "đã xác minh danh tính, được phép đặt mật khẩu mới
# cho user này" giữa 2 bước của luồng quên mật khẩu (xem forgot_password_view/
# reset_password_view) - hết hạn sau RESET_VERIFIED_TTL_SECONDS để không giữ
# quyền đặt lại mật khẩu vô thời hạn trên một trình duyệt dùng chung.
RESET_VERIFIED_USER_KEY = "password_reset_verified_user_id"
RESET_VERIFIED_AT_KEY = "password_reset_verified_at"
RESET_VERIFIED_TTL_SECONDS = 10 * 60


def register_view(request):
    if request.user.is_authenticated:
        return redirect("products:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Phải lấy session_key TRƯỚC khi gọi login() - xem giải thích
            # chi tiết trong cart/services.py::merge_guest_cart_into_user.
            guest_session_key = request.session.session_key
            user = form.save()
            # post_save signal (accounts/signals.py) đã tự tạo sẵn Wallet/
            # Favorite/Cart cho user này, nên ở đây chỉ cần đăng nhập luôn.
            login(request, user)
            # Gộp giỏ hàng khách vãng lai (nếu trình duyệt này đã thêm sản
            # phẩm từ trước khi đăng ký) vào giỏ hàng vừa tạo cho tài khoản.
            merge_guest_cart_into_user(guest_session_key, user)
            messages.success(request, f"Chào mừng {user.username} đã tham gia Astraea!")
            return redirect("products:home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("products:home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Phải lấy session_key TRƯỚC khi gọi login() - xem giải thích
            # chi tiết trong cart/services.py::merge_guest_cart_into_user.
            guest_session_key = request.session.session_key
            user = form.get_user()
            login(request, user)
            merge_guest_cart_into_user(guest_session_key, user)
            messages.success(request, "Đăng nhập thành công.")
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url:
                return redirect(next_url)
            # Tài khoản quản trị (is_staff) đăng nhập ở form khách hàng này
            # thì vào thẳng trang quản trị luôn, thay vì rơi vào trang chủ
            # như một khách hàng bình thường - admin vẫn có thể bấm "XEM
            # TRANG WEB" (link có sẵn của Django admin) để xem/thao tác như
            # khách khi cần test.
            if user.is_staff:
                return redirect("admin:index")
            return redirect("products:home")
    else:
        form = AuthenticationForm(request)

    return render(request, "accounts/login.html", {"form": form})


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect("products:home")

    if request.method == "POST":
        form = ForgotPasswordVerifyForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            request.session[RESET_VERIFIED_USER_KEY] = user.pk
            request.session[RESET_VERIFIED_AT_KEY] = time.time()
            return redirect("accounts:reset_password")
    else:
        form = ForgotPasswordVerifyForm()

    return render(request, "accounts/forgot_password.html", {"form": form})


def reset_password_view(request):
    verified_user_id = request.session.get(RESET_VERIFIED_USER_KEY)
    verified_at = request.session.get(RESET_VERIFIED_AT_KEY)
    session_expired = (
        not verified_user_id
        or not verified_at
        or time.time() - verified_at > RESET_VERIFIED_TTL_SECONDS
    )
    if session_expired:
        messages.error(request, "Phiên xác minh đã hết hạn, vui lòng thử lại.")
        return redirect("accounts:forgot_password")

    target_user = get_object_or_404(User, pk=verified_user_id)

    if request.method == "POST":
        form = SetNewPasswordForm(target_user, request.POST)
        if form.is_valid():
            form.save()
            del request.session[RESET_VERIFIED_USER_KEY]
            del request.session[RESET_VERIFIED_AT_KEY]
            messages.success(request, "Đặt lại mật khẩu thành công, vui lòng đăng nhập lại.")
            return redirect("accounts:login")
    else:
        form = SetNewPasswordForm(target_user)

    return render(request, "accounts/reset_password.html", {"form": form, "target_user": target_user})


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật hồ sơ cá nhân.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})
