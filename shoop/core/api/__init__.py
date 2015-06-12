# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.api.factories import viewset_factory
from shoop.core.api.orders import OrderViewSet
from shoop.core.api.products import ProductViewSet, ShopProductViewSet
from shoop.core.models import Contact, Shop
from shoop.core.models.categories import Category


def populate_core_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shoop/category", viewset_factory(Category))
    router.register("shoop/contact", viewset_factory(Contact))
    router.register("shoop/order", OrderViewSet)
    router.register("shoop/product", ProductViewSet)
    router.register("shoop/shop", viewset_factory(Shop))
    router.register("shoop/shop_product", ShopProductViewSet)
