from django.contrib import admin

from .models import GlassesOverlay


@admin.register(GlassesOverlay)
class GlassesOverlayAdmin(admin.ModelAdmin):
    list_display = ("product", "width_ratio", "vertical_offset", "updated_at")
    search_fields = ("product__name",)
    autocomplete_fields = ("product",)
