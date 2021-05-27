# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView

from shuup.admin.shop_provider import get_shop
from shuup.admin.supplier_provider import get_supplier
from shuup.admin.utils.urls import get_model_url
from shuup.core.models import ShopProduct
from shuup.core.specs.product_kind import DefaultProductKindSpec, get_product_kind_specs
from shuup.utils.django_compat import reverse


class ProductDeleteView(DetailView):
    model = ShopProduct
    context_object_name = "product"
    product_listing_names = [DefaultProductKindSpec.admin_listing_name]

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(shop=get_shop(self.request), product__kind__in=self.get_listing_product_kinds_values())
        )

        supplier = get_supplier(self.request)
        if supplier:
            qs = qs.filter(suppliers=supplier)

        return qs

    def get_listing_product_kinds_values(self):
        return [
            product_kind_spec.value
            for product_kind_spec in get_product_kind_specs()
            if product_kind_spec.admin_listing_name in self.product_listing_names
        ]

    def get(self, request, *args, **kwargs):
        product = self.get_object().product
        return HttpResponseRedirect(get_model_url(product, shop=self.request.shop))

    def post(self, request, *args, **kwargs):
        product = self.get_object().product
        product.soft_delete(user=request.user)
        messages.success(request, _("%s has been marked deleted.") % product)
        return HttpResponseRedirect(reverse("shuup_admin:shop_product.list"))
