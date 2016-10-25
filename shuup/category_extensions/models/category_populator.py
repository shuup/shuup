# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db import models

from shuup.category_extensions.models.populator_rules import \
    CategoryPopulatorRule
from shuup.core.models import Category, ShopProduct


class CategoryPopulator(models.Model):
    category = models.OneToOneField(Category)
    rules = models.ManyToManyField(CategoryPopulatorRule)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    def matches_product(self, shop_product):
        return all([populator_rule.matches(shop_product) for populator_rule in self.rules.all()])

    def clear_unmatching(self):
        products = ShopProduct.objects.filter(categories__in=[self.category.pk])
        for product in products:
            product.categories.remove(self.category)

        for rule in self.rules.all():
            products = rule.filter_matches(products)

        for product in products:
            product.categories.add(self.category)
