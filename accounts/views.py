from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from cart.services import merge_guest_cart_into_user

from .forms import ProfileForm, RegisterForm


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
