from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("dang-ky/", views.register_view, name="register"),
    path("dang-nhap/", views.login_view, name="login"),
    path("dang-xuat/", LogoutView.as_view(), name="logout"),
    path("quen-mat-khau/", views.forgot_password_view, name="forgot_password"),
    path("dat-lai-mat-khau/", views.reset_password_view, name="reset_password"),
    path("ho-so/", views.profile_view, name="profile"),
]
