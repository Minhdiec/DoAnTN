from django.contrib import admin

from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    filter_horizontal = ("products",)
    search_fields = ("user__username",)
