"""
Management command: tạo bù Wallet/Cart/Favorite cho những User đang THIẾU 1
trong 3 model này.

Vì sao cần: `accounts/signals.py` chỉ tự tạo Wallet/Cart/Favorite khi User
MỚI được tạo (post_save với created=True). Những tài khoản đã tồn tại từ
TRƯỚC KHI signal này được thêm vào (ví dụ superuser tạo lúc mới khởi tạo dự
án) sẽ không có các model này, dẫn tới lỗi "RelatedObjectDoesNotExist: User
has no wallet" khi họ thao tác thanh toán (xem CLAUDE_PROGRESS.md - lỗi
trong BUG.ipynb). Lệnh này quét lại TOÀN BỘ user, bù đắp cho những ai thiếu.

An toàn để chạy nhiều lần (get_or_create, không tạo trùng).

Cách chạy:
    python manage.py backfill_profiles
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from cart.models import Cart
from favorites.models import Favorite
from wallet.models import Wallet

User = get_user_model()


class Command(BaseCommand):
    help = "Tạo bù Wallet/Cart/Favorite cho các User đang thiếu (tài khoản tạo trước khi có signal)."

    def handle(self, *args, **options):
        wallet_count = 0
        cart_count = 0
        favorite_count = 0

        for user in User.objects.all():
            _, created = Wallet.objects.get_or_create(user=user)
            wallet_count += created

            _, created = Cart.objects.get_or_create(user=user)
            cart_count += created

            _, created = Favorite.objects.get_or_create(user=user)
            favorite_count += created

        self.stdout.write(self.style.SUCCESS(
            f"Đã tạo bù: {wallet_count} wallet, {cart_count} giỏ hàng, {favorite_count} danh sách yêu thích."
        ))
