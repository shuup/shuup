# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from shoop.front.template_helpers.general import get_newest_products, get_best_selling_products, get_random_products
from shoop.xtheme.plugins import TemplatedPlugin
from django.utils.translation import ugettext_lazy as _


class ProductHighlightPlugin(TemplatedPlugin):
    identifier = "classic_gray.product_highlight"
    name = _("Product Highlights")
    template_name = "classic_gray/highlight_plugin.jinja"
    fields = [
        ("title", forms.CharField(required=False, initial="")),
        ("type", forms.ChoiceField(choices=[
            ("newest", "Newest"),
            ("best_selling", "Best Selling"),
            ("random", "Random"),
        ], initial="newest")),
        ("count", forms.IntegerField(min_value=1, initial=4))
    ]

    def get_context_data(self, context):
        type = self.config.get("type", "newest")
        count = self.config.get("count", 4)
        if type == "newest":
            products = get_newest_products(context, count)
        elif type == "best_selling":
            products = get_best_selling_products(context, count)
        elif type == "random":
            products = get_random_products(context, count)
        else:
            products = []

        return {
            "request": context["request"],
            "title": self.config.get("title"),
            "products": products
        }
