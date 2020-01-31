# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Shop, ShopStatus
from shuup.core.utils.shops import get_shop_from_host
from shuup.utils.importing import cached_load

SHOP_SESSION_KEY = "admin_shop"


class AdminShopProvider(object):

    def get_shop(self, request):
        if not request.user.is_staff:
            return None

        # take the first if multishop is disabled
        if not settings.SHUUP_ENABLE_MULTIPLE_SHOPS:
            return Shop.objects.first()

        permitted_shops = Shop.objects.get_for_user(request.user).filter(status=ShopStatus.ENABLED)

        if SHOP_SESSION_KEY in request.session:
            shop = Shop.objects.filter(pk=request.session[SHOP_SESSION_KEY]).first()
            if shop and shop in permitted_shops:
                return shop

        # try loading the shop from the host
        host = request.META.get("HTTP_HOST")
        shop = get_shop_from_host(host) if host else None
        if shop and shop in permitted_shops:
            return shop

        # no shop set, fetch the first shop available
        first_available_shop = permitted_shops.first()
        if first_available_shop:
            return first_available_shop

        # so return the first if we are superuser
        if request.user.is_superuser:
            return Shop.objects.first()

    def set_shop(self, request, shop=None):
        if not request.user.is_staff:
            raise PermissionDenied(_("You must have the Access to Admin Panel permission."))

        if shop:
            # only can set if the user is superuser or is the shop staff
            if shop.staff_members.filter(pk=request.user.pk).exists() or request.user.is_superuser:
                request.session[SHOP_SESSION_KEY] = shop.id
            else:
                raise PermissionDenied(_("You must have the Access to Admin Panel permissions to this shop."))

        else:
            self.unset_shop(request)

    def unset_shop(self, request):
        if SHOP_SESSION_KEY in request.session:
            del request.session[SHOP_SESSION_KEY]


def get_shop_provider():
    return cached_load("SHUUP_ADMIN_SHOP_PROVIDER_SPEC")()


def get_shop(request):
    return get_shop_provider().get_shop(request)


def set_shop(request, shop=None):
    return get_shop_provider().set_shop(request, shop)


def unset_shop(request):
    get_shop_provider().unset_shop(request)
