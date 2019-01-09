# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import ShopProduct, ShopProductVisibility, Supplier
from shuup.front.utils.sorts_and_filters import get_form_field_label

from .product_list_modifiers import (
    OneChoiceFilterWidget, SimpleProductListModifier
)


class SupplierProductListFilter(SimpleProductListModifier):
    is_active_key = "filter_products_by_supplier"
    is_active_label = _("Filter products by supplier")
    ordering_key = "filter_products_by_supplier_ordering"
    ordering_label = _("Ordering for filter by supplier")
    label_key = "filter_products_by_supplier_label"

    def get_fields(self, request, category=None):
        shop_products_qs = ShopProduct.objects.filter(
            shop=request.shop
        ).exclude(visibility=ShopProductVisibility.NOT_VISIBLE)

        if category:
            shop_products_qs = shop_products_qs.filter(Q(primary_category=category) | Q(categories=category))

        queryset = Supplier.objects.enabled().filter(
            Q(shop_products__in=shop_products_qs),
            shops=request.shop
        ).distinct()
        if not queryset.exists():
            return

        return [
            (
                "supplier",
                forms.ModelChoiceField(
                    queryset=queryset,
                    empty_label=None,
                    required=False,
                    label=get_form_field_label("supplier", _("Suppliers")),
                    widget=OneChoiceFilterWidget()
                )
            ),
        ]

    def get_filters(self, request, data):
        supplier = data.get("supplier")
        if supplier:
            return Q(shop_products__suppliers=supplier)

    def get_admin_fields(self):
        default_fields = super(SupplierProductListFilter, self).get_admin_fields()
        default_fields[0][1].help_text = _(
            "Check this to allow products to be filterable by supplier."
        )
        default_fields[1][1].help_text = _(
            "Use a numeric value to set the order in which the supplier filters will appear."
        )
        return default_fields
