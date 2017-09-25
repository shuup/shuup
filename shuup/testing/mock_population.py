# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.conf import settings
from django.utils import translation

from shuup.core.models import Category, Product, ShopProduct

from .factories import (
    CategoryFactory, create_default_order_statuses, get_currency,
    get_default_payment_method, get_default_shipping_method, get_default_shop,
    ProductFactory
)


class Populator:
    def __init__(self):
        self.shop = get_default_shop()

    def populate(self):
        translation.activate(settings.LANGUAGES[0][0])

        # Create default objects
        get_default_payment_method()
        get_default_shipping_method()
        create_default_order_statuses()
        get_currency("EUR")
        get_currency("USD")
        get_currency("BRL")
        get_currency("GBP")
        get_currency("CNY")
        get_currency("JPY", digits=0)

        category_created = False
        while Category.objects.count() < 5:
            CategoryFactory()
            category_created = True

        if category_created:
            Category.objects.rebuild()

        while Product.objects.count() < 30:
            product = ProductFactory()
            self.generate_pricing(product)

    def generate_pricing(self, product):
        pass

    def populate_if_required(self):
        if ShopProduct.objects.filter(shop=self.shop).count() < 5:
            self.populate()


def populate_if_required():
    Populator().populate_if_required()
