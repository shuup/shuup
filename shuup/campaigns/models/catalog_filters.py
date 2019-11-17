# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from polymorphic.models import PolymorphicModel

from shuup.core.models import Category, Product, ProductType, Shop, ShopProduct


class CatalogFilter(PolymorphicModel):
    model = None

    identifier = "base_catalog_filter"
    name = _("Base Catalog Filter")

    active = models.BooleanField(default=True, verbose_name=_("active"))

    def filter_queryset(self, queryset):
        raise NotImplementedError(
            "Error! Not implemented: `CatalogFilter` -> `filter_queryset()`. "
            "Subclasses should implement `filter_queryset`."
        )


class ProductTypeFilter(CatalogFilter):
    model = ProductType
    identifier = "product_type_filter"
    name = _("Product type")

    product_types = models.ManyToManyField(ProductType, verbose_name=_("product Types"))

    def get_matching_shop_products(self):
        ids = self.values.values_list("id", flat=True)
        return ShopProduct.objects.filter(product__type_id__in=ids)

    def matches(self, shop_product):
        return (shop_product.product.type_id in self.values.values_list("id", flat=True))

    def filter_queryset(self, queryset):
        return queryset.filter(product__type_id__in=self.values.values_list("id", flat=True))

    @property
    def description(self):
        return _("Limit the campaign only to selected product types.")

    @property
    def values(self):
        return self.product_types

    @values.setter
    def values(self, values):
        self.product_types.set(values)


class ProductFilter(CatalogFilter):
    model = Product
    identifier = "product_filter"
    name = _("Product")

    products = models.ManyToManyField(Product, verbose_name=_("product"))

    def get_matching_shop_products(self):
        ids = self.values.values_list("pk", flat=True)
        return ShopProduct.objects.filter(product__id__in=ids)

    def matches(self, shop_product):
        product_ids = self.values.values_list("pk", flat=True)
        return (shop_product.product.pk in product_ids or shop_product.product.variation_parent_id in product_ids)

    def filter_queryset(self, queryset):
        product_ids = self.products.values_list("id", flat=True)
        return queryset.filter(
            Q(product_id__in=product_ids) | Q(product__variation_parent_id__in=product_ids))

    @property
    def description(self):
        return _("Limit the campaign only to selected products.")

    @property
    def values(self):
        return self.products

    @values.setter
    def values(self, values):
        self.products.set(values)


class CategoryFilter(CatalogFilter):
    model = Category
    identifier = "category_filter"
    name = _("Product Category")

    categories = models.ManyToManyField(Category, verbose_name=_("categories"))

    def get_matching_shop_products(self):
        shop_products = []
        shop = Shop.objects.first()
        cat_ids = self.categories.all_except_deleted().values_list("pk", flat=True)
        for parent in ShopProduct.objects.filter(categories__id__in=cat_ids).select_related("product"):
            shop_products.append(parent)
            for child in parent.product.variation_children.all():
                try:
                    child_sp = child.get_shop_instance(shop)
                except ShopProduct.DoesNotExist:
                    continue
                shop_products.append(child_sp)
        return shop_products

    def matches(self, shop_product):
        ids = list(shop_product.categories.all_except_deleted().values_list("id", flat=True))
        for child in shop_product.product.variation_children.all():
            try:
                child_sp = child.get_shop_instance(shop_product.shop)
            except ShopProduct.DoesNotExist:
                continue

            ids += list(child_sp.categories.all_except_deleted().values_list("id", flat=True))

        if shop_product.product.variation_parent:
            try:
                parent_sp = shop_product.product.variation_parent.get_shop_instance(shop_product.shop)
            except ShopProduct.DoesNotExist:
                pass
            else:
                ids += list(parent_sp.categories.all_except_deleted().values_list("id", flat=True))

        new_ids = self.values.values_list("id", flat=True)
        return bool([x for x in ids if x in new_ids])

    def filter_queryset(self, queryset):
        return queryset.filter(categories__in=self.categories.all_except_deleted())

    @property
    def description(self):
        return _("Limit the campaign only to products in selected categories.")

    @property
    def values(self):
        return self.categories

    @values.setter
    def values(self, values):
        self.categories.set(values)
