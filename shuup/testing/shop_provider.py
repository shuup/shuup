# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import Shop

SHOP_SESSION_KEY = "admin_shop"


class TestingAdminShopProvider(object):
    def get_shop(self, request):
        return Shop.objects.first()

    def set_shop(self, request, shop=None):
        if not request.user.is_staff:
            raise PermissionDenied(_("You must have the Access to Admin Panel permission."))

        if shop:
            request.session[SHOP_SESSION_KEY] = shop.id
        else:
            self.unset_shop(request)

    def unset_shop(self, request):
        if SHOP_SESSION_KEY in request.session:
            del request.session[SHOP_SESSION_KEY]
