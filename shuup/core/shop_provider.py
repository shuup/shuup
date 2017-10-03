# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import Shop
from shuup.utils.importing import cached_load


class DefaultShopProvider(object):
    @classmethod
    def get_shop(cls, request, **kwargs):
        host = request.META.get("HTTP_HOST")
        if not host:
            shop = Shop.objects.first()
        else:
            shop = Shop.objects.filter(domain=host).first()
            if not shop:
                subdomain = host.split(".")[0]
                shop = Shop.objects.filter(domain=subdomain).first()
            if not shop:
                shop = Shop.objects.first()

        return shop


def get_shop(request, **kwargs):
    return cached_load("SHUUP_REQUEST_SHOP_PROVIDER_SPEC").get_shop(request, **kwargs)
