from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """
    Cấu hình cho app "reviews": đánh giá sản phẩm + phân loại cảm xúc.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'
    verbose_name = "Đánh giá sản phẩm"
