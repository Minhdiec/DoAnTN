from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("tao/<int:order_item_id>/", views.review_create, name="create"),
]
