"""
Signal: tự động tạo Wallet, Wishlist, Cart cho mỗi User mới được tạo ra
(dù tạo qua form đăng ký, qua "createsuperuser", hay tạo tay trong /admin).

Nhờ vậy các view ở app "wallet"/"wishlist"/"cart" sau này có thể truy cập
thẳng request.user.wallet / request.user.wishlist / request.user.cart mà
không lo bị lỗi DoesNotExist.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from cart.models import Cart
from wallet.models import Wallet
from wishlist.models import Wishlist


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_related_profiles(sender, instance, created, **kwargs):
    if not created:
        return

    Wallet.objects.get_or_create(user=instance)
    Wishlist.objects.get_or_create(user=instance)
    Cart.objects.get_or_create(user=instance)
