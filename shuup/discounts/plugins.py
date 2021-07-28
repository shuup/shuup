# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shuup.discounts.models import Discount
from shuup.front.template_helpers.general import get_listed_products
from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.plugins.forms import GenericPluginForm, TranslatableField


class ProductSelectionConfigForm(GenericPluginForm):
    """
    A configuration form for the DiscountedProductsPlugin
    """

    def populate(self):
        """
        A custom populate method to display product choices
        """
        for field in self.plugin.fields:
            if isinstance(field, tuple):
                name, value = field
                value.initial = self.plugin.config.get(name, value.initial)
                self.fields[name] = value

        discounts_qs = Discount.objects.filter(
            Q(shop=self.request.shop, active=True),
            Q(Q(product__isnull=False) | Q(category__isnull=False, exclude_selected_category=False)),
        )

        self.fields["discounts"] = forms.ModelMultipleChoiceField(
            queryset=discounts_qs,
            label=_("Discounts"),
            help_text=_(
                "Select all discounts to render products from. Only active discounts that have "
                "product or category linked are available."
            ),
            required=True,
            initial=self.plugin.config.get("discounts", None),
        )

    def clean(self):
        """
        A custom clean method to transform selected discounts into a list of ids
        """
        cleaned_data = super(ProductSelectionConfigForm, self).clean()
        if cleaned_data.get("discounts"):
            cleaned_data["discounts"] = [discount.pk for discount in cleaned_data["discounts"]]
        return cleaned_data


class DiscountedProductsPlugin(TemplatedPlugin):
    identifier = "discount_product"
    name = _("Discounted Products")
    template_name = "shuup/discounts/product_discount_plugin.jinja"
    editor_form_class = ProductSelectionConfigForm
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        (
            "orderable_only",
            forms.BooleanField(
                label=_("Only show in-stock and orderable items"),
                help_text=_(
                    "Warning: The final number of products can be lower than 'Count' "
                    "as it will filter out unorderable products from a set of 'Count' products."
                ),
                initial=True,
                required=False,
            ),
        ),
    ]

    def get_context_data(self, context):
        count = self.config.get("count", 4)
        orderable_only = self.config.get("orderable_only", True)
        discounts = self.config.get("discounts")
        products = []

        if discounts:
            # make sure to have only available discounts
            discounts = Discount.objects.available(shop=context["request"].shop).filter(pk__in=discounts)
            extra_filters = Q(
                Q(product_discounts__in=discounts) | Q(shop_products__categories__category_discounts__in=discounts)
            )
            products = get_listed_products(context, count, orderable_only=orderable_only, extra_filters=extra_filters)

        return {"request": context["request"], "title": self.get_translated_value("title"), "products": products}
