# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum

from shuup.core.models import Product, ProductCrossSell, ProductCrossSellType
from shuup.front.template_helpers.general import (
    get_best_selling_products,
    get_newest_products,
    get_products_for_categories,
    get_random_products,
)
from shuup.front.template_helpers.product import get_product_cross_sells, map_relation_type
from shuup.xtheme import TemplatedPlugin
from shuup.xtheme.plugins.forms import GenericPluginForm, TranslatableField
from shuup.xtheme.plugins.widgets import XThemeSelect2ModelChoiceField, XThemeSelect2ModelMultipleChoiceField


class HighlightType(Enum):
    NEWEST = "newest"
    BEST_SELLING = "best_selling"
    RANDOM = "random"

    class Labels:
        NEWEST = _("Newest")
        BEST_SELLING = _("Best Selling")
        RANDOM = _("Random")


class ProductHighlightPlugin(TemplatedPlugin):
    identifier = "async_product_highlight"
    name = _("Product Highlights (asynchronous)")
    template_name = "shuup/xtheme/plugins/highlight_plugin_async.jinja"
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        (
            "type",
            forms.ChoiceField(label=_("Type"), choices=HighlightType.choices(), initial=HighlightType.NEWEST.value),
        ),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=5)),
        ("cutoff_days", forms.IntegerField(label=_("Cutoff days"), min_value=1, initial=30)),
        ("cache_timeout", forms.IntegerField(label=_("Cache timeout (seconds)"), min_value=0, initial=120)),
    ]

    def get_context_data(self, context):
        request = context["request"]
        plugin_type = self.config.get("type", HighlightType.NEWEST.value)
        count = self.config.get("count", 5)
        cutoff_days = self.config.get("cutoff_days", 30)
        cache_timeout = self.config.get("cache_timeout", 0)
        orderable_only = False

        products = []
        if request.is_ajax():
            if plugin_type == HighlightType.NEWEST.value:
                products = get_newest_products(context, count, orderable_only)
            elif plugin_type == HighlightType.BEST_SELLING.value:
                products = get_best_selling_products(context, count, cutoff_days, orderable_only)
            elif plugin_type == HighlightType.RANDOM.value:
                products = get_random_products(context, count, orderable_only)

        return {
            "request": request,
            "title": self.get_translated_value("title"),
            "products": products,
            "data_url": reverse(
                "shuup:xtheme-product-highlight",
                kwargs=dict(plugin_type=plugin_type, cutoff_days=cutoff_days, count=count, cache_timeout=cache_timeout),
            ),
        }


class ProductCrossSellsPlugin(TemplatedPlugin):
    identifier = "async_product_cross_sells"
    name = _("Product Cross Sells (asynchronous)")
    template_name = "shuup/xtheme/plugins/highlight_plugin_async.jinja"
    required_context_variables = ["product"]
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("type", ProductCrossSell.type.field.formfield()),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=5)),
        (
            "use_variation_parents",
            forms.BooleanField(
                label=_("Show variation parents"),
                help_text=_("Render variation parents instead of the children."),
                initial=False,
                required=False,
            ),
        ),
        ("cache_timeout", forms.IntegerField(label=_("Cache timeout (seconds)"), min_value=0, initial=120)),
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
        request = context["request"]
        products = []
        use_variation_parents = self.config.get("use_variation_parents", False)
        count = self.config.get("count", 5)
        cache_timeout = self.config.get("cache_timeout", 0)
        product = context.get("product", self.config.get("product"))

        orderable_only = False
        relation_type = self.config.get("type")
        try:
            relation_type = map_relation_type(relation_type)
        except LookupError:
            relation_type = ProductCrossSellType.RELATED

        if request.is_ajax() and product:
            if not isinstance(product, Product):
                product = Product.objects.filter(id=product).first()

            if product:
                products = get_product_cross_sells(
                    context,
                    product,
                    relation_type,
                    count=count,
                    orderable_only=orderable_only,
                    use_variation_parents=use_variation_parents,
                )

        return {
            "request": context["request"],
            "title": self.get_translated_value("title"),
            "products": products,
            "data_url": reverse(
                "shuup:xtheme-product-cross-sells-highlight",
                kwargs=dict(
                    product_id=product.id,
                    relation_type=relation_type.label,
                    use_parents=(1 if use_variation_parents else 0),
                    count=count,
                    cache_timeout=cache_timeout,
                ),
            )
            if product
            else "/",
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
            initial=self.plugin.config.get("category") if self.plugin else None,
        )


class ProductsFromCategoryPlugin(TemplatedPlugin):
    identifier = "async_category_products"
    name = _("Category Products Highlight (asynchronous)")
    template_name = "shuup/xtheme/plugins/highlight_plugin_async.jinja"
    editor_form_class = ProductsFromCategoryForm
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("count", forms.IntegerField(label=_("Count"), min_value=1, initial=5)),
        ("cache_timeout", forms.IntegerField(label=_("Cache timeout (seconds)"), min_value=0, initial=120)),
    ]

    def get_context_data(self, context):
        request = context["request"]
        products = []
        category_id = self.config.get("category")
        count = self.config.get("count", 5)
        cache_timeout = self.config.get("cache_timeout", 0)
        orderable_only = False

        if request.is_ajax() and category_id:
            products = get_products_for_categories(
                context, [category_id], n_products=count, orderable_only=orderable_only
            )

        return {
            "request": request,
            "title": self.get_translated_value("title"),
            "products": products,
            "data_url": reverse(
                "shuup:xtheme-category-products-highlight",
                kwargs=dict(category_id=category_id, count=count, cache_timeout=cache_timeout),
            ),
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
            extra_widget_attrs={"data-search-mode": "main"},
        )


class ProductSelectionPlugin(TemplatedPlugin):
    """
    A plugin that renders a selection of products
    """

    identifier = "async_product_selection"
    name = _("Product Selection (asynchronous)")
    template_name = "shuup/xtheme/plugins/highlight_plugin_async.jinja"
    editor_form_class = ProductSelectionConfigForm
    fields = [
        ("title", TranslatableField(label=_("Title"), required=False, initial="")),
        ("cache_timeout", forms.IntegerField(label=_("Cache timeout (seconds)"), min_value=0, initial=120)),
    ]

    def get_context_data(self, context):
        request = context["request"]
        products = self.config.get("products", [])
        cache_timeout = self.config.get("cache_timeout", 0)
        products_qs = Product.objects.none()

        if request.is_ajax() and products:
            products_qs = Product.objects.listed(shop=request.shop, customer=request.customer).filter(pk__in=products)

        return {
            "request": request,
            "title": self.get_translated_value("title"),
            "products": products_qs,
            "data_url": reverse(
                "shuup:xtheme-product-selections-highlight",
                kwargs=dict(
                    product_ids=",".join([(str(prod.pk) if hasattr(prod, "pk") else str(prod)) for prod in products]),
                    cache_timeout=cache_timeout,
                ),
            ),
        }
