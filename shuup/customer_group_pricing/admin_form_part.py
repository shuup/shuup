# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.core.models import ContactGroup
from shuup.customer_group_pricing.models import CgpDiscount, CgpPrice


class CustomerGroupPricingForm(forms.Form):
    def __init__(self, **kwargs):
        self.product = kwargs.pop("product", None)
        self.request = kwargs.pop("request", None)
        self.shop = kwargs.pop('shop', None)
        super(CustomerGroupPricingForm, self).__init__(**kwargs)
        self.groups = []
        if not self.shop:
            self.shop = self.request.shop
        if self.product:
            self._build_fields()

    def _build_fields(self):
        self.groups = list(ContactGroup.objects.filter(
            Q(price_display_options__show_pricing=True) |
            Q(
                id__in=CgpPrice.objects.filter(product=self.product)
                .values_list("group_id", flat=True)
            )
        ).distinct())
        prices_by_shop_and_group = dict(
            ((shop_id or 0, group_id or 0), price)
            for (shop_id, group_id, price)
            in CgpPrice.objects.filter(product=self.product)
            .values_list("shop_id", "group_id", "price_value")
        )

        for group in self.groups:
            shop_group_id_tuple = self._get_id_tuple(self.shop, group)
            name = self._get_field_name(shop_group_id_tuple)
            price = prices_by_shop_and_group.get(shop_group_id_tuple)
            price_field = forms.DecimalField(
                min_value=0, initial=price,
                label=(_("Price (%(shop)s/%(group)s)") % {"shop": self.shop, "group": group}),
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
            CgpPrice.objects.filter(product=self.product, group=group, shop=shop).delete()
        else:
            (spp, created) = CgpPrice.objects.get_or_create(
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
            self._process_single_save(self.shop, group)

    def get_shop_group_field(self, shop, group):
        shop_group_id_tuple = self._get_id_tuple(shop, group)
        name = self._get_field_name(shop_group_id_tuple)
        return self[name]


class CustomerGroupDiscountForm(forms.Form):
    def __init__(self, **kwargs):
        self.product = kwargs.pop("product", None)
        self.request = kwargs.pop("request", None)
        self.shop = kwargs.pop('shop', None)
        super(CustomerGroupDiscountForm, self).__init__(**kwargs)
        self.groups = []

        if not self.shop:
            self.shop = self.request.shop

        if self.product:
            self._build_fields()

    def _build_fields(self):
        self.groups = list(ContactGroup.objects.filter(
            Q(price_display_options__show_pricing=True) |
            Q(
                id__in=CgpDiscount.objects.filter(product=self.product)
                .values_list("group_id", flat=True)
            )
        ).distinct())
        discounts_by_shop_and_group = dict(
            ((shop_id or 0, group_id or 0), discount_amount)
            for (shop_id, group_id, discount_amount)
            in CgpDiscount.objects.filter(product=self.product)
            .values_list("shop_id", "group_id", "discount_amount_value")
        )

        for group in self.groups:
            shop_group_id_tuple = self._get_id_tuple(self.shop, group)
            name = self._get_field_name(shop_group_id_tuple)
            discount_amount = discounts_by_shop_and_group.get(shop_group_id_tuple)
            discount_amount_field = forms.DecimalField(
                min_value=0, initial=discount_amount,
                label=(_("Discount (%(shop)s/%(group)s)") % {"shop": self.shop, "group": group}),
                required=False
            )
            self.fields[name] = discount_amount_field

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
            CgpDiscount.objects.filter(product=self.product, group=group, shop=shop).delete()
        else:
            (spd, created) = CgpDiscount.objects.get_or_create(
                product=self.product, group=group, shop=shop,
                defaults={'discount_amount_value': value})
            if not created:
                spd.discount_amount_value = value
                spd.save()

    def save(self):
        if not self.has_changed():  # No changes, so no need to do anything.
            # (This is required because `.full_clean()` would create an empty `.cleaned_data`,
            #  but short-circuits out if `has_changed()` returns false.
            #  That, in kind, would cause `self.cleaned_data.get(name)` in `_process_single_save`
            #  to return Nones, clearing out all prices. Oops.)
            return

        for group in self.groups:
            self._process_single_save(self.shop, group)

    def get_shop_group_field(self, shop, group):
        shop_group_id_tuple = self._get_id_tuple(shop, group)
        name = self._get_field_name(shop_group_id_tuple)
        return self[name]


class CustomerGroupPricingFormPart(FormPart):
    priority = 10

    def get_form_defs(self):
        yield TemplatedFormDef(
            name="customer_group_pricing",
            form_class=CustomerGroupPricingForm,
            template_name="shuup/admin/customer_group_pricing/price_form_part.jinja",
            required=False,
            kwargs={"product": self.object.product, "request": self.request}
        )

    def form_valid(self, form):
        form["customer_group_pricing"].save()


class CustomerGroupPricingDiscountFormPart(FormPart):
    priority = 11

    def get_form_defs(self):
        yield TemplatedFormDef(
            name="customer_group_discount",
            form_class=CustomerGroupDiscountForm,
            template_name="shuup/admin/customer_group_pricing/discount_form_part.jinja",
            required=False,
            kwargs={"product": self.object.product, "request": self.request}
        )

    def form_valid(self, form):
        form["customer_group_discount"].save()
