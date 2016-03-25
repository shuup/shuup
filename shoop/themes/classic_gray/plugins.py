# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import ProductCrossSellType
from shoop.front.template_helpers.general import (
    get_best_selling_products, get_newest_products, get_random_products
)
from shoop.xtheme import TemplatedPlugin
from shoop.xtheme.plugins.forms import TranslatableField


class ProductHighlightPlugin(TemplatedPlugin):
    identifier = "classic_gray.product_highlight"
    name = _("Product Highlights")
    template_name = "classic_gray/highlight_plugin.jinja"
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("type", forms.ChoiceField(label=_("Type"), choices=[
            ("newest", "Newest"),
            ("best_selling", "Best Selling"),
            ("random", "Random"),
        ], initial="newest")),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        ("orderable_only", forms.BooleanField(label=_("Only show in-stock and orderable items"),
                                              initial=True,
                                              required=False))
    ]

    def get_context_data(self, context):
        type = self.config.get("type", "newest")
        count = self.config.get("count", 4)
        orderable_only = self.config.get("orderable_only", True)
        if type == "newest":
            products = get_newest_products(context, count, orderable_only)
        elif type == "best_selling":
            products = get_best_selling_products(context, count, orderable_only)
        elif type == "random":
            products = get_random_products(context, count, orderable_only)
        else:
            products = []

        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "products": products
        }


class ProductCrossSellsPlugin(TemplatedPlugin):
    identifier = "classic_gray.product_cross_sells"
    name = _("Product Cross Sells")
    template_name = "classic_gray/cross_sells_plugin.jinja"
    required_context_variables = ["product"]
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("type", forms.ChoiceField(label=_("Type"), choices=[
            (ProductCrossSellType.RELATED, "Related"),
            (ProductCrossSellType.RECOMMENDED, "Recommended"),
            (ProductCrossSellType.BOUGHT_WITH, "Bought With"),
        ], initial="related")),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        ("orderable_only", forms.BooleanField(label=_("Only show in-stock and orderable items"),
                                              initial=True,
                                              required=False))
    ]

    def get_context_data(self, context):
        count = self.config.get("count", 4)
        product = context.get("product", None)
        orderable_only = self.config.get("orderable_only", True)
        type = self.config.get("type", "related")

        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "product": product,
            "type": type,
            "count": count,
            "orderable_only": orderable_only,
        }
