# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum

from shuup.core.models import Product, ProductCrossSell, ProductCrossSellType
from shuup.front.template_helpers.general import (
    get_best_selling_products, get_newest_products,
    get_products_for_categories, get_random_products
)
from shuup.front.template_helpers.product import map_relation_type
from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.plugins.forms import GenericPluginForm, TranslatableField
from shuup.xtheme.plugins.widgets import (
    XThemeSelect2ModelChoiceField, XThemeSelect2ModelMultipleChoiceField
)


class HighlightType(Enum):
    NEWEST = "newest"
    BEST_SELLING = "best_selling"
    RANDOM = "random"

    class Labels:
        NEWEST = _("Newest")
        BEST_SELLING = _("Best Selling")
        RANDOM = _("Random")


class ProductHighlightPlugin(TemplatedPlugin):
    identifier = "product_highlight"
    name = _("Product Highlights")
    template_name = "shuup/xtheme/plugins/highlight_plugin.jinja"
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("type", forms.ChoiceField(
            label=_("Type"),
            choices=HighlightType.choices(),
            initial=HighlightType.NEWEST.value
        )),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        ("orderable_only", forms.BooleanField(
            label=_("Only show in-stock and orderable items"),
            help_text=_(
                "Warning: The final number of products can be lower than 'Count' "
                "as it will filter out unorderable products from a set of 'Count' products."
            ),
            initial=True, required=False
        ))
    ]

    def get_context_data(self, context):
        highlight_type = self.config.get("type", HighlightType.NEWEST.value)
        count = self.config.get("count", 4)
        orderable_only = self.config.get("orderable_only", True)

        if highlight_type == HighlightType.NEWEST.value:
            products = get_newest_products(context, count, orderable_only)
        elif highlight_type == HighlightType.BEST_SELLING.value:
            products = get_best_selling_products(
                context,
                count,
                orderable_only=orderable_only,
            )
        elif highlight_type == HighlightType.RANDOM.value:
            products = get_random_products(context, count, orderable_only)
        else:
            products = []

        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "products": products
        }


class ProductCrossSellsPlugin(TemplatedPlugin):
    identifier = "product_cross_sells"
    name = _("Product Cross Sells")
    template_name = "shuup/xtheme/plugins/cross_sells_plugin.jinja"
    required_context_variables = ["product"]
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("type", ProductCrossSell.type.field.formfield()),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        ("orderable_only", forms.BooleanField(
            label=_("Only show in-stock and orderable items"),
            initial=True, required=False,
            help_text=_(
                "Warning: The final number of products can be lower than 'Count' "
                "as it will filter out unorderable products from a set of 'Count' products."
            )
        ))
    ]

    def __init__(self, config):
        relation_type = config.get("type", None)
        if relation_type:
            # Map initial config string to enum type
            try:
                type = map_relation_type(relation_type)
            except LookupError:
                type = ProductCrossSellType.RELATED
            config["type"] = type
        super(ProductCrossSellsPlugin, self).__init__(config)

    def get_context_data(self, context):
        count = self.config.get("count", 4)
        product = context.get("product", None)
        orderable_only = self.config.get("orderable_only", True)
        relation_type = self.config.get("type")
        try:
            type = map_relation_type(relation_type)
        except LookupError:
            type = ProductCrossSellType.RELATED
        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "product": product,
            "type": type,
            "count": count,
            "orderable_only": orderable_only,
        }


class ProductsFromCategoryForm(GenericPluginForm):
    def populate(self):
        for field in self.plugin.fields:
            if isinstance(field, tuple):
                name, value = field
                value.initial = self.plugin.config.get(name, value.initial)
                self.fields[name] = value

        self.fields["category"] = XThemeSelect2ModelChoiceField(
            model="shuup.category",
            label=_("Category"),
            required=False,
            initial=self.plugin.config.get("category") if self.plugin else None
        )


class ProductsFromCategoryPlugin(TemplatedPlugin):
    identifier = "category_products"
    name = _("Category Products Highlight")
    template_name = "shuup/xtheme/plugins/highlight_plugin.jinja"
    editor_form_class = ProductsFromCategoryForm
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=4)),
        ("orderable_only", forms.BooleanField(
            label=_("Only show in-stock and orderable items"),
            initial=True, required=False,
            help_text=_(
                "Warning: The final number of products can be lower than 'Count' "
                "as it will filter out unorderable products from a set of 'Count' products."
            )
        ))
    ]

    def get_context_data(self, context):
        products = []
        category_id = self.config.get("category")
        count = self.config.get("count")
        orderable_only = self.config.get("orderable_only", True)

        if category_id:
            products = get_products_for_categories(
                context,
                [category_id],
                n_products=count,
                orderable_only=orderable_only
            )
        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "products": products
        }


class ProductSelectionConfigForm(GenericPluginForm):
    """
    A configuration form for the ProductSelectionPlugin
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

        self.fields["products"] = XThemeSelect2ModelMultipleChoiceField(
            model="shuup.product",
            label=_("Products"),
            help_text=_("Select all products you want to show"),
            required=True,
            initial=self.plugin.config.get("products"),
            extra_widget_attrs={
                "data-search-mode": "main"
            }
        )


class ProductSelectionPlugin(TemplatedPlugin):
    """
    A plugin that renders a selection of products
    """
    identifier = "product_selection"
    name = _("Product Selection")
    template_name = "shuup/xtheme/plugins/product_selection_plugin.jinja"
    editor_form_class = ProductSelectionConfigForm
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial=""))
    ]

    def get_context_data(self, context):
        request = context["request"]
        products = self.config.get("products")
        products_qs = Product.objects.none()

        if products:
            products_qs = Product.objects.listed(
                shop=request.shop,
                customer=request.customer
            ).filter(shop_products__pk__in=products)

        return {
            "request": request,
            "title": self.get_translated_value("title"),
            "products": products_qs
        }
