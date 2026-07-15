from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("products:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # post_save signal (accounts/signals.py) đã tự tạo sẵn Wallet/
            # Wishlist/Cart cho user này, nên ở đây chỉ cần đăng nhập luôn.
            login(request, user)
            messages.success(request, f"Chào mừng {user.username} đã tham gia ChuyenDeTN Shop!")
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
            login(request, form.get_user())
            messages.success(request, "Đăng nhập thành công.")
            next_url = request.POST.get("next") or request.GET.get("next")
            return redirect(next_url or "products:home")
    else:
        form = AuthenticationForm(request)

    return render(request, "accounts/login.html", {"form": form})
