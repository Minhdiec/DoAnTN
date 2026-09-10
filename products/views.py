from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render

from favorites.models import Favorite
from orders.models import Order, OrderItem
from reviews.forms import ReviewForm
from reviews.models import Review
from tryon.models import GlassesOverlay

from .models import Category, Product


def _favorite_product_ids(request):
    # Tính 1 LẦN duy nhất cho cả trang (không phải mỗi thẻ sản phẩm tự query
    # riêng) - dùng chung cho home/search/detail để nút trái tim
    # (products/_favorite_button.html) biết sản phẩm nào cần tô đậm sẵn.
    if not request.user.is_authenticated:
        return set()
    favorite = Favorite.objects.filter(user=request.user).first()
    return set(favorite.products.values_list("id", flat=True)) if favorite else set()


def home(request):
    categories = list(Category.objects.all())
    # Ảnh đại diện cho mỗi danh mục ở khu "Danh mục nổi bật": lấy ảnh sản
    # phẩm THẬT mới nhất trong danh mục đó (không cần thêm trường ảnh riêng
    # cho Category) - danh mục nào chưa có sản phẩm nào có ảnh thì vẫn hiện
    # avatar chữ cái như cũ (xử lý ở template).
    for category in categories:
        sample_product = (
            Product.objects.filter(category=category, is_active=True)
            .exclude(image="")
            .order_by("-created_at")
            .first()
        )
        category.sample_image = sample_product.image if sample_product else None

    featured_products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .order_by("-created_at")
    )
    context = {
        "categories": categories,
        "featured_products": featured_products,
        "gender_choices": Product.Gender.choices,
        "favorite_product_ids": _favorite_product_ids(request),
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

    # Sản phẩm này CÓ THỂ chưa có ảnh AR (chỉ 2/3 sản phẩm demo hiện có ảnh
    # PNG kính thật - xem CLAUDE_PROGRESS.md mục 25) - dùng try/except thay
    # vì truy cập trực tiếp product.glasses_overlay khi không tồn tại sẽ ném
    # GlassesOverlay.DoesNotExist (quan hệ OneToOne "ngược" không tự trả về
    # None như ForeignKey thường).
    try:
        product_glasses_overlay = product.glasses_overlay
    except GlassesOverlay.DoesNotExist:
        product_glasses_overlay = None

    reviews = (
        product.reviews.select_related("user").prefetch_related("media").order_by("-created_at")
    )

    # Một aggregate() duy nhất lấy TẤT CẢ số liệu cần cho khu vực đánh giá
    # (điểm trung bình, tổng số, số lượng theo từng mức sao, số lượng theo
    # từng nhãn cảm xúc) - tránh chạy nhiều query COUNT() rời rạc.
    stats = reviews.aggregate(
        average=Avg("rating"),
        total=Count("id"),
        star_5=Count("id", filter=Q(rating=5)),
        star_4=Count("id", filter=Q(rating=4)),
        star_3=Count("id", filter=Q(rating=3)),
        star_2=Count("id", filter=Q(rating=2)),
        star_1=Count("id", filter=Q(rating=1)),
        positive=Count("id", filter=Q(sentiment="POS")),
        neutral=Count("id", filter=Q(sentiment="NEU")),
        negative=Count("id", filter=Q(sentiment="NEG")),
    )

    rating_total = stats["total"] or 0
    rating_distribution = [
        {
            "star": star,
            "count": stats[f"star_{star}"],
            "percent": round(stats[f"star_{star}"] / rating_total * 100) if rating_total else 0,
        }
        for star in range(5, 0, -1)
    ]

    sentiment_stats = None
    if rating_total:
        sentiment_stats = {
            "positive_percent": round(stats["positive"] / rating_total * 100),
            "neutral_percent": round(stats["neutral"] / rating_total * 100),
            "negative_percent": round(stats["negative"] / rating_total * 100),
        }

    # Ô nhập bình luận/đánh giá CHỈ hiện khi: đã đăng nhập + đã mua sản phẩm
    # này qua một đơn đã GIAO THÀNH CÔNG + chưa đánh giá sản phẩm này lần
    # nào (mỗi sản phẩm đã mua chỉ đánh giá được 1 lần).
    can_review = False
    review_order_item = None
    if request.user.is_authenticated:
        already_reviewed = Review.objects.filter(user=request.user, product=product).exists()
        if not already_reviewed:
            review_order_item = OrderItem.objects.filter(
                order__user=request.user,
                order__status=Order.Status.DELIVERED,
                product=product,
            ).first()
            can_review = review_order_item is not None

    context = {
        "product": product,
        "gallery_images": product.images.all(),
        "related_products": related_products,
        "product_glasses_overlay": product_glasses_overlay,
        # Toàn bộ mẫu kính AR đang có (không chỉ của sản phẩm này) - hiển thị
        # trong gallery bên trong khu vực thử kính để người dùng so sánh
        # được nhiều mẫu khác nhau ngay trên 1 trang sản phẩm, giống hệt
        # GlassesPicker của prototype (CLAUDE_PROGRESS.md mục 20/22).
        "tryon_gallery": GlassesOverlay.objects.select_related("product").all(),
        "reviews": reviews,
        "rating_average": round(stats["average"], 1) if stats["average"] else 0,
        "rating_average_rounded": round(stats["average"]) if stats["average"] else 0,
        "rating_total": rating_total,
        "rating_distribution": rating_distribution,
        "sentiment_stats": sentiment_stats,
        "can_review": can_review,
        "review_order_item": review_order_item,
        "review_form": ReviewForm() if can_review else None,
        "favorite_product_ids": _favorite_product_ids(request),
    }
    return render(request, "products/detail.html", context)


def search(request):
    # Ô tìm kiếm ở header (templates/base.html) trỏ về đây, gửi từ khóa qua
    # tham số "q" (GET) - dùng GET (không phải POST) đúng chuẩn cho 1 hành
    # động TÌM (không thay đổi dữ liệu gì), giúp có thể copy/chia sẻ link
    # kết quả tìm kiếm hoặc bấm nút Back của trình duyệt hoạt động đúng.
    query = request.GET.get("q", "").strip()

    products = Product.objects.filter(is_active=True).select_related("category")
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )
    products = products.order_by("-created_at")

    context = {
        "query": query,
        "products": products,
        "favorite_product_ids": _favorite_product_ids(request),
    }
    return render(request, "products/search.html", context)
