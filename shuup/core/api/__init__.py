# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.api.factories import viewset_factory
from shuup.core.api.contacts import ContactViewSet
from shuup.core.api.orders import OrderViewSet
from shuup.core.api.products import ProductViewSet, ShopProductViewSet
from shuup.core.models import Category, Shop


def populate_core_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shuup/category", viewset_factory(Category))
    router.register("shuup/contact", ContactViewSet)
    router.register("shuup/order", OrderViewSet)
    router.register("shuup/product", ProductViewSet)
    router.register("shuup/shop", viewset_factory(Shop))
    router.register("shuup/shop_product", ShopProductViewSet)
