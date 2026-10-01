from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from tryon.models import GlassesOverlay

from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Mỗi danh mục là một DÁNG KÍNH (Square, Oval, Round, Rectangle...).
    list_display = ("name", "slug", "product_count", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_product_count=Count("products"))

    @admin.display(description="Số sản phẩm", ordering="_product_count")
    def product_count(self, obj):
        return obj._product_count


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "position")
    readonly_fields = ("preview",)

    @admin.display(description="Xem trước")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px;">', obj.image.url)
        return "-"


class GlassesOverlayInline(admin.StackedInline):
    # Ảnh PNG nền trong suốt dùng cho nút "TRY ON" (thử kính ảo).
    model = GlassesOverlay
    extra = 0
    max_num = 1
    fields = ("preview", "image", "width_ratio", "vertical_offset")
    readonly_fields = ("preview",)

    @admin.display(description="Xem trước")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="height:60px;background:#e0ac8c;padding:4px;border-radius:4px;">',
                obj.image.url,
            )
        return "-"


class HasTryOnFilter(admin.SimpleListFilter):
    title = "Thử kính ảo"
    parameter_name = "tryon"

    def lookups(self, request, model_admin):
        return (("yes", "Có"), ("no", "Chưa có"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(glasses_overlay__isnull=False)
        if self.value() == "no":
            return queryset.filter(glasses_overlay__isnull=True)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail",
        "name",
        "sku",
        "category",
        "gender",
        "price",
        "stock_quantity",
        "has_tryon",
        "is_active",
    )
    list_display_links = ("thumbnail", "name")
    list_filter = ("category", "gender", "is_active", HasTryOnFilter)
    list_editable = ("stock_quantity", "is_active")
    search_fields = ("name", "sku", "description")
    list_select_related = ("category", "glasses_overlay")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ("Thông tin chung", {"fields": ("name", "slug", "sku", "category", "gender", "is_active")}),
        ("Giá và kho", {"fields": ("price", "stock_quantity")}),
        ("Hình ảnh", {"fields": ("image_preview", "image")}),
        ("Mô tả", {"fields": ("description", "specs", "care_instructions")}),
    )
    readonly_fields = ("image_preview",)
    inlines = [ProductImageInline, GlassesOverlayInline]

    @admin.display(description="Ảnh")
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;">', obj.image.url)
        return "-"

    @admin.display(description="Ảnh hiện tại")
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:160px;border-radius:6px;">', obj.image.url)
        return "-"

    @admin.display(description="Try on", boolean=True)
    def has_tryon(self, obj):
        return hasattr(obj, "glasses_overlay")
