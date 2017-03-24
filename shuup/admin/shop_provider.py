# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup import configuration
from shuup.core.models import Shop
from shuup.utils.importing import load


class AdminShopProvider(object):

    def get_shop(self, request):
        return Shop.objects.first()

    def set_shop(self, request, shop=None):
        pass

    def unset_shop(self, request):
        pass

    def _get_shop_provider(self):
        return configuration.get(None, "admin_shop_provider")

    def _get_shop_provider_shop(self, request):
        provider_cls = self._get_shop_provider()
        if provider_cls:
            provider = load(provider_cls)
            return provider().get_shop(request)

    def _set_shop_provider_shop(self, request, shop):
        provider_cls = self._get_shop_provider()
        if provider_cls:
            provider = load(provider_cls)
            return provider().set_shop(request, shop)

    def get_provided_shop(self, request):
        shop = self._get_shop_provider_shop(request)
        if not shop:
            shop = self.get_shop(request)
        return shop

    def set_provided_shop(self, request, shop=None):
        provided_shop = self._set_shop_provider_shop(request, shop)
        if not provided_shop:
            provided_shop = self.set_shop(request, shop)
        return provided_shop


def get_shop(request):
    return AdminShopProvider().get_provided_shop(request)


def set_shop(request, shop=None):
    return AdminShopProvider().set_provided_shop(request, shop)


def unset_shop(request):
    AdminShopProvider().unset_shop(request)
