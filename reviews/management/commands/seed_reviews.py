"""
Management command: tạo dữ liệu ảo cho tính năng đánh giá sản phẩm (BƯỚC 6,
xem CLAUDE_PROGRESS.md mục 30) - vì đánh giá giờ yêu cầu "đã mua VÀ đơn đã
giao thành công", seed phải dựng đủ chuỗi: user ảo -> đơn hàng ảo (giao
thành công) -> đánh giá ảo, rồi chạy predict_sentiment() y hệt luồng thật để
gắn nhãn cảm xúc (không tự gán nhãn tay).

Mỗi user ảo mua TẤT CẢ sản phẩm đang bán trong 1 đơn hàng duy nhất, rồi đánh
giá từng sản phẩm với một trong các mẫu câu khen/chê/trung lập có sẵn - tỉ lệ
được chọn xấp xỉ đúng tỉ lệ nhãn của bộ dữ liệu huấn luyện thật (POS ~60%,
NEG ~24%, NEU ~16%, xem phantichcamxuc/sentiment_analysis.ipynb).

LƯU Ý: seed KHÔNG trừ tồn kho sản phẩm thật (khác với luồng đặt hàng thật ở
orders/views.py) - mục đích chỉ là có đủ đánh giá để demo thống kê, không
phải mô phỏng một nền kinh tế cửa hàng thật, nên không nên làm cạn kho vì lý
do này.

Cách chạy:
    python manage.py seed_reviews            # tạo mới (bỏ qua nếu đã có)
    python manage.py seed_reviews --reset     # xóa sạch user ảo cũ rồi tạo lại
"""

import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Order, OrderItem
from products.models import Product
from reviews.ml.sentiment import predict_sentiment
from reviews.models import Review

User = get_user_model()

# Hậu tố email dùng chung cho toàn bộ user ảo - "@gmail.com" để trông giống
# tài khoản thật khi hiển thị công khai trên trang đánh giá (username vẫn
# KHÔNG dùng tiền tố "seed_..." lộ liễu). Việc nhận diện/dọn dẹp user ảo
# (--reset) dựa vào SEED_USERNAMES, không dựa vào hậu tố email.
SEED_EMAIL_SUFFIX = "@gmail.com"
SEED_PASSWORD = "seed12345"

SEED_USERNAMES = [
    "minhanh97", "quangtran_hcm", "thuha.pham", "hoangnam88", "linhchi_vu",
    "duchuy2000", "thanhmai_nguyen", "baotran99", "khanhly_dep", "vietanh92",
    "ngocbich.tran", "hoainam_le", "phuongthao96", "gianguyen_hn", "tuankiet.vo",
]

# SĐT ảo tương ứng theo đúng thứ tự SEED_USERNAMES (đầu số di động Việt Nam
# hợp lệ), để trang quản trị/đơn hàng không hiển thị SĐT trống cho user ảo.
SEED_PHONE_NUMBERS = [
    "0901234567", "0912345678", "0923456789", "0934567890", "0945678901",
    "0356789012", "0367890123", "0378901234", "0389012345", "0790123456",
    "0812345678", "0823456789", "0834567890", "0845678901", "0856789012",
]

# (rating tối thiểu, rating tối đa, danh sách nội dung) - nội dung là câu
# tiếng Việt thật về kính mắt, đa dạng khen/chê/trung lập giống văn phong bộ
# dữ liệu huấn luyện, để predict_sentiment() dự đoán ra đúng 3 nhãn tự nhiên.
REVIEW_POOLS = [
    (
        0.60,  # tỉ lệ ~ nhãn POS trong dữ liệu train
        (4, 5),
        [
            "Chất lượng sản phẩm tuyệt vời, gọng kính chắc chắn, đeo rất vừa mặt, quá ưng ý!",
            "Kính đẹp y như hình, đóng gói cẩn thận, giao hàng nhanh, sẽ ủng hộ shop dài dài.",
            "Chất liệu cao cấp, tròng kính chống UV tốt, đeo cả ngày không bị mỏi, đáng tiền.",
            "Thiết kế sang trọng, màu sắc y hình, nhân viên tư vấn nhiệt tình, quá hài lòng.",
            "Gọng kính nhẹ, ôm mặt thoải mái, chất lượng vượt mong đợi so với giá tiền.",
            "Giao hàng cực nhanh, kính đẹp hơn mong đợi, chắc chắn sẽ mua thêm mẫu khác.",
        ],
    ),
    (
        0.16,  # tỉ lệ ~ nhãn NEU
        (3, 3),
        [
            "Sản phẩm tạm ổn, không có gì đặc biệt, giao hàng đúng hẹn.",
            "Chất lượng ở mức bình thường so với giá tiền, dùng tạm được.",
            "Kính dùng được nhưng gọng hơi lỏng, chưa thật sự ấn tượng.",
            "Giao hàng hơi chậm nhưng sản phẩm đúng như mô tả trên web.",
            "Mẫu mã bình thường, không quá đẹp nhưng cũng không tệ.",
            "Đóng gói tạm ổn, chất lượng ở mức chấp nhận được.",
        ],
    ),
    (
        0.24,  # tỉ lệ ~ nhãn NEG
        (1, 2),
        [
            "Gọng kính lỏng lẻo, đeo được vài ngày đã hỏng, rất thất vọng.",
            "Hàng không giống hình quảng cáo, chất lượng kém, không đáng số tiền bỏ ra.",
            "Giao sai mẫu, tròng kính bị trầy xước sẵn, quá tệ.",
            "Đóng gói cẩu thả, kính bị móp méo khi nhận hàng, rất bực mình.",
            "Chất lượng tệ hơn mong đợi rất nhiều, không recommend cho ai cả.",
            "Giao hàng chậm trễ, liên hệ shop không phản hồi, trải nghiệm rất tệ.",
        ],
    ),
]

ANONYMOUS_PROBABILITY = 0.3


class Command(BaseCommand):
    help = "Tạo user/đơn hàng/đánh giá ảo (đã gán nhãn cảm xúc) để demo tính năng đánh giá."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Xóa toàn bộ user ảo (và đơn hàng/đánh giá kèm theo) đã seed trước đó rồi tạo lại từ đầu.",
        )

    def handle(self, *args, **options):
        products = list(Product.objects.filter(is_active=True))
        if not products:
            self.stdout.write(self.style.WARNING("Chưa có sản phẩm nào đang bán, dừng lại."))
            return

        if options["reset"]:
            deleted, _ = User.objects.filter(username__in=SEED_USERNAMES).delete()
            self.stdout.write(self.style.WARNING(f"Đã xóa {deleted} bản ghi liên quan tới user ảo cũ."))

        review_count = 0
        sentiment_tally = {"POS": 0, "NEU": 0, "NEG": 0}

        with transaction.atomic():
            for username, phone_number in zip(SEED_USERNAMES, SEED_PHONE_NUMBERS):
                expected_email = f"{username}{SEED_EMAIL_SUFFIX}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={"email": expected_email, "phone_number": phone_number},
                )
                if created:
                    user.set_password(SEED_PASSWORD)
                    user.save(update_fields=["password"])
                # post_save signal (accounts/signals.py) đã tự tạo Wallet/Cart/Favorite.
                else:
                    # User ảo đã tồn tại từ lần seed trước (có thể còn email/
                    # SĐT cũ) - đồng bộ lại cho khớp dữ liệu seed hiện tại mà
                    # KHÔNG đụng tới đơn hàng/đánh giá đã tạo trước đó.
                    update_fields = []
                    if user.email != expected_email:
                        user.email = expected_email
                        update_fields.append("email")
                    if user.phone_number != phone_number:
                        user.phone_number = phone_number
                        update_fields.append("phone_number")
                    if update_fields:
                        user.save(update_fields=update_fields)

                # Chỉ mua/đánh giá những sản phẩm CHƯA có đánh giá của user này -
                # tránh chạy lại lệnh nhiều lần lại tạo thêm đơn hàng trống
                # (đơn hàng phải luôn đi kèm ít nhất 1 đánh giá thật sự mới).
                pending_products = [
                    p for p in products if not Review.objects.filter(user=user, product=p).exists()
                ]
                if not pending_products:
                    continue

                order_total = sum((p.price for p in pending_products), Decimal("0.00"))
                order = Order.objects.create(user=user, total_amount=order_total)
                order_items_by_product = {
                    product.id: OrderItem.objects.create(
                        order=order, product=product, quantity=1, unit_price=product.price
                    )
                    for product in pending_products
                }

                for product in pending_products:
                    rating, content = self._pick_review()
                    sentiment, confidence = predict_sentiment(content)

                    Review.objects.create(
                        product=product,
                        user=user,
                        order_item=order_items_by_product[product.id],
                        rating=rating,
                        content=content,
                        is_anonymous=random.random() < ANONYMOUS_PROBABILITY,
                        sentiment=sentiment,
                        sentiment_confidence=confidence,
                    )
                    review_count += 1
                    sentiment_tally[sentiment] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Hoàn tất: {len(SEED_USERNAMES)} user ảo, {review_count} đánh giá mới "
            f"(POS {sentiment_tally['POS']} · NEU {sentiment_tally['NEU']} · NEG {sentiment_tally['NEG']})."
        ))

    def _pick_review(self):
        # random.choices theo trọng số ~ tỉ lệ nhãn thật để phân bố sao/cảm
        # xúc của dữ liệu seed tự nhiên giống dữ liệu huấn luyện thật.
        weights = [pool[0] for pool in REVIEW_POOLS]
        _, (min_rating, max_rating), contents = random.choices(REVIEW_POOLS, weights=weights, k=1)[0]
        rating = random.randint(min_rating, max_rating)
        content = random.choice(contents)
        return rating, content
