# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.views.generic import DetailView

from shuup.front.models import StoredBasket
from shuup.utils.importing import cached_load, load


class CartDetailView(DetailView):
    model = StoredBasket
    template_name = "shuup/front/admin/stored_basket_detail.jinja"

    def get_queryset(self):
        qs = super(CartDetailView, self).get_queryset()
        return qs.prefetch_related("products")

    def get_context_data(self, **kwargs):
        context = super(CartDetailView, self).get_context_data(**kwargs)
        basket_class = None
        if self.object.class_spec:
            basket_class = load(self.object.class_spec)

        if not basket_class:
            basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")

        basket = basket_class(self.request, basket_name=self.object.key, shop=self.object.shop)
        context["basket"] = basket

        sources = [
            basket.shipping_address,
            basket.billing_address,
            basket.customer,
            basket.orderer,
        ]

        fields = ("email", "phone", "tax_number")

        for field in fields:
            for source in sources:
                val = getattr(source, field, None)
                if val:
                    context[field] = val
                    break

        return context
