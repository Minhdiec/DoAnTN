"""
Signal: tự động tạo Wallet, Favorite, Cart cho mỗi User mới được tạo ra
(dù tạo qua form đăng ký, qua "createsuperuser", hay tạo tay trong /admin).

Nhờ vậy các view ở app "wallet"/"favorites"/"cart" sau này có thể truy cập
thẳng request.user.wallet / request.user.favorites / request.user.cart mà
không lo bị lỗi DoesNotExist.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from cart.models import Cart
from favorites.models import Favorite
from wallet.models import Wallet


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_related_profiles(sender, instance, created, **kwargs):
    if not created:
        return

    Wallet.objects.get_or_create(user=instance)
    Favorite.objects.get_or_create(user=instance)
    Cart.objects.get_or_create(user=instance)
