from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.my_orders, name="my_orders"),
    path("dat-hang/", views.checkout, name="checkout"),
    path("huy/<int:order_id>/", views.cancel_order, name="cancel"),
]
