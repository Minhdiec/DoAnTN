from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.home, name="home"),
    path("tim-kiem/", views.search, name="search"),
    path("san-pham/<slug:slug>/", views.detail, name="detail"),
]
