# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import ManyToManyField

from shuup.apps.provides import get_provide_objects
from shuup.core.models import Category, Product, ProductType, ShopProduct


def get_matching_for_product(shop_product, provide_category, skippable_classes=None):
    """
    Get matching ids for shop product based on provide category

    For example:
    matching_ids = get_matching_for_product(shop_product, "campaign_catalog_filter")

    :param shop_product: A Shop Product
    :type shop_product: shuup.core.models.ShopProduct
    :param provide_category: Provide category name
    :type provide_category: str
    :param skip: Classes to skip
    :type skip: None or list
    :return: list of collected item ids
    :rtype: list[int]
    """
    collected = set()
    matcher = ProductCampaignMatcher(shop_product)
    for item in get_provide_objects(provide_category):
        if skippable_classes:
            objects = item._meta.model.objects.not_instance_of(*skippable_classes).all()
        else:
            objects = item._meta.model.objects.all()
        for obj in objects:
            if matcher.matches(obj):
                collected.add(obj.pk)
    return collected


class ProductCampaignMatcher(object):
    """
    A class to match shop product to existing campaigns
    """

    def __init__(self, shop_product, **kwargs):
        """
        :param shop_product: a Shop Product to find matches for
        :type shop_product: shuup.core.models.ShopProduct
        """
        assert isinstance(shop_product, ShopProduct)

        self.shop = shop_product.shop
        self.product = shop_product.product
        self.shop_product = shop_product

    def matches(self, obj):
        """
        Tries to match filters, conditions, effects etc to shop product

        :return: True or False based on the match
        :rtype: bool
        """
        _matches = []
        for field in obj._meta.get_fields():
            related_model = field.related_model
            if self._is_product_kind(related_model):
                _matches.append(self.product_matcher(field, obj))
            elif self._is_category(related_model):
                _matches.append(self.category_matcher(field, obj))
            elif self._is_product_type(related_model):
                _matches.append(self.product_type_matcher(field, obj))
            else:
                _matches.append(False)
        return any(_matches)

    def product_type_matcher(self, field, obj):
        if isinstance(field, ManyToManyField):
            return self._product_types_match(field.name, obj)
        else:
            return self._product_type_matches(field.name, obj)

    def category_matcher(self, field, obj):
        if isinstance(field, ManyToManyField):
            return self._categories_match(field.name, obj)
        else:
            return self._category_matches(field.name, obj)

    def product_matcher(self, field, obj):
        if isinstance(field, ManyToManyField):
            return self._products_match(field, obj)
        else:
            return self._product_matches(field, obj)

    def _product_types_match(self, field_name, obj):
        return getattr(obj, field_name).filter(pk=self.product.type.pk).exists()

    def _product_type_matches(self, field_name, obj):
        attr = getattr(obj, field_name)
        if not attr:
            return False
        return (self.product.type.pk == attr.pk)

    def _products_match(self, field, obj):
        attr = getattr(obj, field.name)
        if not attr:
            return False
        if self._is_product(field.related_model):
            return attr.filter(pk=self.product.pk).exists()
        elif self._is_shop_product(field.related_model):
            return attr.filter(product__id=self.product.pk).exists()
        return False

    def _product_matches(self, field, obj):
        attr = getattr(obj, field.name)
        if not attr:
            return False
        if self._is_product(field.related_model):
            return (self.product.pk == attr.pk)
        elif self._is_shop_product(field.related_model):
            return (self.product.pk == attr.product.pk)
        return False

    def _categories_match(self, field_name, obj):
        existing = set(getattr(obj, field_name).values_list("pk", flat=True))
        if self.shop_product.primary_category and self.shop_product.primary_category.pk in existing:
            return True
        cats = set(self.shop_product.categories.values_list("pk", flat=True))
        if cats.intersection(existing):
            return True
        return False

    def _category_matches(self, field_name, obj):
        attr = getattr(obj, field_name)
        if not attr:
            return False
        if self.shop_product.primary_category and self.shop_product.primary_category.pk == attr.pk:
            return True
        return self.shop_product.categories.filter(pk=attr.pk).exists()

    def _is_product_kind(self, model):
        return (self._is_product(model) or self._is_shop_product(model))

    def _is_product(self, model):
        if model is None:
            return False
        return isinstance(model(), Product)

    def _is_shop_product(self, model):
        if model is None:
            return False
        return isinstance(model(), ShopProduct)

    def _is_category(self, model):
        if model is None:
            return False
        return isinstance(model(), Category)

    def _is_product_type(self, model):
        if model is None:
            return False
        return isinstance(model(), ProductType)
