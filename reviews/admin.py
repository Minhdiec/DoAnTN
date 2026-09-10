from django.contrib import admin
from django.db.models import Count, Q

from .models import Review, ReviewMedia


class ReviewMediaInline(admin.TabularInline):
    model = ReviewMedia
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "user",
        "rating",
        "sentiment",
        "sentiment_confidence",
        "is_anonymous",
        "created_at",
    )
    list_filter = ("sentiment", "rating", "is_anonymous", "product")
    search_fields = ("product__name", "user__username", "content")
    inlines = [ReviewMediaInline]
    change_list_template = "admin/reviews/review/change_list.html"

    def has_add_permission(self, request):
        # Đánh giá CHỈ được tạo qua reviews/views.py (đã mua + đơn giao thành
        # công + chạy mô hình cảm xúc) - admin bịa ra 1 đánh giá từ trang này
        # là sai logic nghiệp vụ (khách mới là người viết đánh giá), nên bỏ
        # hẳn nút "Thêm" thay vì để đó rồi không ai được dùng đúng cách.
        return False

    def has_change_permission(self, request, obj=None):
        # Tương tự: không cho SỬA nội dung/sao/nhãn cảm xúc của khách qua
        # admin (đó là dữ liệu khách tạo ra, admin chỉ nên XEM để kiểm duyệt).
        # Vẫn xem được chi tiết (chỉ đọc) và XÓA được nếu cần gỡ đánh giá vi
        # phạm - has_view_permission mặc định vẫn đúng khi change trả False.
        return False

    def changelist_view(self, request, extra_context=None):
        # Thống kê % tích cực/trung lập/tiêu cực theo đúng bộ lọc hiện tại
        # trên trang (nếu admin đang lọc theo sản phẩm/sao thì thống kê cũng
        # tính trên đúng tập đang xem, không phải toàn bộ bảng).
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            queryset = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response

        # .aggregate() (khác .values().annotate()) luôn ra ĐÚNG MỘT dòng tổng,
        # không bị dính lỗi GROUP BY kế thừa order_by như bên dưới.
        totals = queryset.aggregate(
            total=Count("id"),
            positive=Count("id", filter=Q(sentiment="POS")),
            neutral=Count("id", filter=Q(sentiment="NEU")),
            negative=Count("id", filter=Q(sentiment="NEG")),
        )
        total = totals["total"]
        response.context_data["sentiment_stats"] = {
            "total": total,
            "positive": totals["positive"],
            "neutral": totals["neutral"],
            "negative": totals["negative"],
            "positive_percent": round(totals["positive"] / total * 100) if total else 0,
            "neutral_percent": round(totals["neutral"] / total * 100) if total else 0,
            "negative_percent": round(totals["negative"] / total * 100) if total else 0,
        }

        # Thống kê CHI TIẾT TỪNG SẢN PHẨM (biểu đồ cột CSS thuần - dự án chủ
        # trương không phụ thuộc thư viện JS vẽ biểu đồ ngoài, xem đầu file
        # static/css/style.css). order_by("product__name") ở đây khớp ĐÚNG
        # với field đang group by (values("product__name")) nên không bị lỗi
        # GROUP BY kế thừa order_by như đã gặp ở phần tổng hợp phía trên.
        product_rows = (
            queryset.order_by("product__name")
            .values("product__name")
            .annotate(
                total=Count("id"),
                positive=Count("id", filter=Q(sentiment="POS")),
                neutral=Count("id", filter=Q(sentiment="NEU")),
                negative=Count("id", filter=Q(sentiment="NEG")),
            )
        )
        product_breakdown = sorted(
            (
                {
                    "name": row["product__name"],
                    "total": row["total"],
                    "positive_percent": round(row["positive"] / row["total"] * 100) if row["total"] else 0,
                    "neutral_percent": round(row["neutral"] / row["total"] * 100) if row["total"] else 0,
                    "negative_percent": round(row["negative"] / row["total"] * 100) if row["total"] else 0,
                }
                for row in product_rows
            ),
            key=lambda row: row["total"],
            reverse=True,
        )
        response.context_data["product_breakdown"] = product_breakdown
        return response
