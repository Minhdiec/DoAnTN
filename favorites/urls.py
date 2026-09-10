from django.urls import path

from . import views

app_name = "favorites"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("bat-tat/<slug:product_slug>/", views.toggle, name="toggle"),
]
