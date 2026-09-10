"""
View cho app "reviews": lưu đánh giá sản phẩm.

Ô nhập đánh giá nằm NGAY TRÊN trang chi tiết sản phẩm (không phải trang
riêng) - xem products/views.py (tính can_review/review_order_item) và
templates/products/detail.html (render form). View này chỉ xử lý POST rồi
quay lại đúng trang sản phẩm đó; GET (ví dụ ai đó dán thẳng link) chỉ
redirect về trang sản phẩm, không có gì để hiển thị riêng.

Điều kiện đánh giá (kiểm tra phía server, không chỉ ẩn nút trên giao diện):
đã đăng nhập, order_item thuộc về chính người dùng, đơn hàng đã giao thành
công, và sản phẩm này chưa được người dùng đánh giá lần nào.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from orders.models import Order, OrderItem

from .forms import ReviewForm
from .ml.sentiment import predict_sentiment
from .models import Review, ReviewMedia

MAX_MEDIA_FILES = 5


def _product_detail_url(product, anchor="danh-gia"):
    return f"{reverse('products:detail', args=[product.slug])}#{anchor}"


@login_required
def review_create(request, order_item_id):
    order_item = get_object_or_404(
        OrderItem.objects.select_related("order", "product"),
        pk=order_item_id,
        order__user=request.user,
    )
    product = order_item.product

    if request.method != "POST":
        return redirect("products:detail", slug=product.slug)

    if order_item.order.status != Order.Status.DELIVERED:
        messages.error(request, "Chỉ đánh giá được sản phẩm trong đơn đã giao thành công.")
        return redirect("orders:my_orders")

    if Review.objects.filter(user=request.user, product=product).exists():
        messages.error(request, f"Bạn đã đánh giá \"{product.name}\" rồi.")
        return redirect(_product_detail_url(product))

    form = ReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Vui lòng chọn số sao (1-5) và nhập nội dung đánh giá.")
        return redirect(_product_detail_url(product))

    review = form.save(commit=False)
    review.product = product
    review.user = request.user
    review.order_item = order_item

    # Mô hình học máy tự động gán nhãn cảm xúc ngay khi lưu đánh giá,
    # người dùng không tự chọn nhãn này.
    review.sentiment, review.sentiment_confidence = predict_sentiment(review.content)
    review.save()

    media_files = request.FILES.getlist("media_files")[:MAX_MEDIA_FILES]
    for uploaded_file in media_files:
        is_image = (uploaded_file.content_type or "").startswith("image/")
        ReviewMedia.objects.create(
            review=review,
            file=uploaded_file,
            media_type=ReviewMedia.MediaType.IMAGE if is_image else ReviewMedia.MediaType.VIDEO,
        )

    messages.success(request, "Cảm ơn bạn đã đánh giá sản phẩm!")
    return redirect(_product_detail_url(product))
