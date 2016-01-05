# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import random

from django.conf import settings
from django.utils import translation

from shoop.core.models import Category, Product, ShopProduct

from .factories import (
    CategoryFactory, create_default_order_statuses, get_default_customer_group,
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
        if "shoop.simple_pricing" in settings.INSTALLED_APPS:
            from shoop.simple_pricing.models import SimpleProductPrice
            SimpleProductPrice.objects.create(
                product=product,
                price_value=random.randint(15, 340),
                shop=get_default_shop(),
                group=get_default_customer_group()
            )

    def populate_if_required(self):
        if ShopProduct.objects.filter(shop=self.shop).count() < 5:
            self.populate()


def populate_if_required():
    Populator().populate_if_required()
