from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def home(request):
    categories = Category.objects.all()
    featured_products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .order_by("-created_at")
    )
    context = {
        "categories": categories,
        "featured_products": featured_products,
        "gender_choices": Product.Gender.choices,
    }
    return render(request, "products/home.html", context)


def detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"),
        slug=slug,
        is_active=True,
    )
    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)
        .select_related("category")[:4]
    )
    context = {
        "product": product,
        "gallery_images": product.images.all(),
        "related_products": related_products,
    }
    return render(request, "products/detail.html", context)
