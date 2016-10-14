# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import csv

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from shuup.admin.modules.settings import ViewSettings
from shuup.admin.utils.picotable import (
    PicotableFileMassAction, PicotableMassAction, PicotableRedirectMassAction
)
from shuup.core.models import Product, ShopProduct, ShopProductVisibility


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


class FileResponseAction(PicotableFileMassAction):
    label = _("Export CSV")
    identifier = "mass_action_product_simple_csv"

    def process(self, request, ids):
        view_settings = ViewSettings(Product, [])
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response, delimiter=";")
        writer.writerow([col.title for col in view_settings.columns])
        for product in Product.objects.filter(id__in=ids):
            row = []
            for dr in [col.id for col in view_settings.columns]:
                row.append(getattr(product, dr))
            writer.writerow(row)
        return response


class EditProductAttributesAction(PicotableRedirectMassAction):
    label = _("Edit products")
    identifier = "mass_action_edit_product"
    redirect_url = reverse("shuup_admin:product.mass_edit")
