# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel

from shuup.core.models import Category, Product, ProductType


class CatalogFilter(PolymorphicModel):
    model = None

    identifier = "base_catalog_filter"
    name = _("Base Catalog Filter")

    active = models.BooleanField(default=True, verbose_name=_("active"))

    def filter_queryset(self, queryset):
        raise NotImplementedError("Subclasses should implement `filter_queryset`")


class ProductTypeFilter(CatalogFilter):
    model = ProductType
    identifier = "product_type_filter"
    name = _("Product type")

    product_types = models.ManyToManyField(ProductType, verbose_name=_("product Types"))

    def matches(self, shop_product):
        return (shop_product.type_id in self.values.values_list("id", flat=True))

    def filter_queryset(self, queryset):
        return queryset.filter(product__type_id__in=self.values.values_list("id", flat=True))

    @property
    def description(self):
        return _("Limit the campaign to selected product types.")

    @property
    def values(self):
        return self.product_types

    @values.setter
    def values(self, values):
        self.product_types = values


class ProductFilter(CatalogFilter):
    model = Product
    identifier = "product_filter"
    name = _("Product")

    products = models.ManyToManyField(Product, verbose_name=_("product"))

    def matches(self, shop_product):
        return (shop_product.pk in self.values.values_list("pk", flat=True))

    def filter_queryset(self, queryset):
        return queryset.filter(product_id__in=self.products.values_list("id", flat=True))

    @property
    def description(self):
        return _("Limit the campaign to selected products.")

    @property
    def values(self):
        return self.products

    @values.setter
    def values(self, values):
        self.products = values


class CategoryFilter(CatalogFilter):
    model = Category
    identifier = "category_filter"
    name = _("Product Category")

    categories = models.ManyToManyField(Category, verbose_name=_("categories"))

    def matches(self, shop_product):
        ids = shop_product.categories.values_list("id", flat=True)
        new_ids = self.values.values_list("id", flat=True)
        return bool([x for x in ids if x in new_ids])

    def filter_queryset(self, queryset):
        return queryset.filter(categories__in=self.categories.all())

    @property
    def description(self):
        return _("Limit the campaign to products in selected categories.")

    @property
    def values(self):
        return self.categories

    @values.setter
    def values(self, values):
        self.categories = values
