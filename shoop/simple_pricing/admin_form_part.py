# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shoop.admin.form_part import FormPart, TemplatedFormDef
from shoop.core.models import ContactGroup, Shop
from shoop.simple_pricing.models import SimpleProductPrice


class SimplePricingForm(forms.Form):
    def __init__(self, **kwargs):
        self.product = kwargs.pop("product", None)
        super(SimplePricingForm, self).__init__(**kwargs)
        self.shops = []
        self.groups = []
        if self.product:
            self._build_fields()

    def _build_fields(self):
        self.shops = list(Shop.objects.all())
        self.groups = list(ContactGroup.objects.filter(
            Q(show_pricing=True) |
            Q(
                id__in=SimpleProductPrice.objects.filter(product=self.product)
                .values_list("group_id", flat=True).distinct()
            )
        ))
        prices_by_shop_and_group = dict(
            ((shop_id or 0, group_id or 0), price)
            for (shop_id, group_id, price)
            in SimpleProductPrice.objects.filter(product=self.product)
            .values_list("shop_id", "group_id", "price_value")
        )

        for group in self.groups:
            for shop in self.shops:
                shop_group_id_tuple = self._get_id_tuple(shop, group)
                name = self._get_field_name(shop_group_id_tuple)
                price = prices_by_shop_and_group.get(shop_group_id_tuple)
                price_field = forms.DecimalField(
                    min_value=0, initial=price,
                    label=(_("Price (%(shop)s/%(group)s)") %
                           {"shop": shop, "group": group}),
                    required=False
                )
                self.fields[name] = price_field

    def _get_id_tuple(self, shop, group):
        return (
            shop.id if shop else 0,
            group.id if group else 0
        )

    def _get_field_name(self, id_tuple):
        return "s_%d_g_%d" % id_tuple

    def _process_single_save(self, shop, group):
        shop_group_id_tuple = self._get_id_tuple(shop, group)
        name = self._get_field_name(shop_group_id_tuple)
        value = self.cleaned_data.get(name)
        clear = (value is None or value < 0)
        if clear:
            SimpleProductPrice.objects.filter(product=self.product, group=group, shop=shop).delete()
        else:
            (spp, created) = SimpleProductPrice.objects.get_or_create(
                product=self.product, group=group, shop=shop,
                defaults={'price_value': value})
            if not created:
                spp.price_value = value
                spp.save()

    def save(self):
        if not self.has_changed():  # No changes, so no need to do anything.
            # (This is required because `.full_clean()` would create an empty `.cleaned_data`,
            #  but short-circuits out if `has_changed()` returns false.
            #  That, in kind, would cause `self.cleaned_data.get(name)` in `_process_single_save`
            #  to return Nones, clearing out all prices. Oops.)
            return

        for group in self.groups:
            for shop in self.shops:
                self._process_single_save(shop, group)

    def get_shop_group_field(self, shop, group):
        shop_group_id_tuple = self._get_id_tuple(shop, group)
        name = self._get_field_name(shop_group_id_tuple)
        return self[name]


class SimplePricingFormPart(FormPart):
    priority = 10

    def get_form_defs(self):
        yield TemplatedFormDef(
            name="simple_pricing",
            form_class=SimplePricingForm,
            template_name="shoop/admin/simple_pricing/form_part.jinja",
            required=False,
            kwargs={"product": self.object}
        )

    def form_valid(self, form):
        form["simple_pricing"].save()
