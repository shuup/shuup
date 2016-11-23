# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import (
    PicotableMassAction, PicotableRedirectMassAction
)
from shuup.core.models import ShopProduct, ShopProductVisibility


class VisibleMassAction(PicotableMassAction):
    label = _("Set visible")
    identifier = "mass_action_product_visible"

    def process(self, request, ids):
        ShopProduct.objects.filter(product__pk__in=ids).update(visibility=ShopProductVisibility.ALWAYS_VISIBLE)


class InvisibleMassAction(PicotableMassAction):
    label = _("Set invisible")
    identifier = "mass_action_product_invisible"

    def process(self, request, ids):
        ShopProduct.objects.filter(product__pk__in=ids).update(visibility=ShopProductVisibility.NOT_VISIBLE)


class EditProductAttributesAction(PicotableRedirectMassAction):
    label = _("Edit products")
    identifier = "mass_action_edit_product"
    redirect_url = reverse("shuup_admin:product.mass_edit")
