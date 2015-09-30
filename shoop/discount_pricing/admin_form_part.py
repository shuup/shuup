# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.core.models import Shop
from shoop.discount_pricing.models import DiscountedProductPrice


class DiscountPricingForm(forms.Form):
    def __init__(self, **kwargs):
        self.product = kwargs.pop("product")
        super(DiscountPricingForm, self).__init__(**kwargs)
        self.shops = []
        if self.product:
            self._build_fields()

    def _build_fields(self):
        self.shops = list(Shop.objects.all())

        prices_by_shop_and_group = dict(
            (shop_id, price)
            for (shop_id, price)
            in DiscountedProductPrice.objects.filter(product=self.product)
            .values_list("shop_id", "price_value")
        )

        for shop in self.shops:
            name = self._get_field_name(shop)
            price = prices_by_shop_and_group.get(shop.id)
            price_field = forms.DecimalField(
                min_value=0, initial=price,
                label=_("Price (%s)") % shop, required=False
            )
            self.fields[name] = price_field

    def _get_field_name(self, shop):
        return "s_%d" % shop.id

    def _process_single_save(self, shop):
        name = self._get_field_name(shop)
        value = self.cleaned_data.get(name)
        clear = (value is None or value < 0)
        if clear:
            DiscountedProductPrice.objects.filter(product=self.product, shop=shop).delete()
        else:
            (spp, created) = DiscountedProductPrice.objects.get_or_create(
                product=self.product, shop=shop,
                defaults={'price_value': value})
            if not created:
                spp.price_value = value
                spp.save()

    def save(self):
        if not self.has_changed():  # No changes, so no need to do anything.
            return

        for shop in self.shops:
            self._process_single_save(shop)

    def get_shop_field(self, shop):
        name = self._get_field_name(shop)
        return self[name]


class DiscountPricingFormPart(FormPart):
    priority = 10

    def get_form_defs(self):
        yield TemplatedFormDef(
            name="discount_pricing",
            form_class=DiscountPricingForm,
            template_name="shoop/admin/discount_pricing/form_part.jinja",
            required=False,
            kwargs={"product": self.object}
        )

    def form_valid(self, form):
        form["discount_pricing"].save()
