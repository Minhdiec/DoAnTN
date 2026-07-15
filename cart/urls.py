from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_view, name="view"),
    path("them/<slug:product_slug>/", views.cart_add, name="add"),
    path("cap-nhat/<int:item_id>/", views.cart_update, name="update"),
    path("xoa/<int:item_id>/", views.cart_remove, name="remove"),
]
