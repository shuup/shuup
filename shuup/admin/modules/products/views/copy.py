# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.shop_provider import get_shop
from shuup.admin.supplier_provider import get_supplier
from shuup.admin.utils.urls import get_model_url
from shuup.core.models import ShopProduct
from shuup.utils.importing import cached_load


class ProductCopyView(DetailView):
    model = ShopProduct
    context_object_name = "product"

    def get_success_url(self, copied_shop_product: ShopProduct):
        return get_model_url(copied_shop_product, shop=get_shop(self.request))

    def get(self, request, *args, **kwargs):
        shop_product = self.get_object()
        current_supplier = None if request.user.is_superuser else get_supplier(request)
        cloner = cached_load("SHUUP_ADMIN_PRODUCT_CLONER")(request.shop, current_supplier)
        copied_shop_product = cloner.clone_product(shop_product=shop_product)
        messages.success(
            request, _("{product_name} was successfully copied".format(product_name=copied_shop_product.product))
        )
        return HttpResponseRedirect(self.get_success_url(copied_shop_product))
