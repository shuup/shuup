# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.api.factories import viewset_factory
from shoop.simple_pricing.models import SimpleProductPrice


def populate_simple_pricing_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shoop/simple_product_price", viewset_factory(SimpleProductPrice))
