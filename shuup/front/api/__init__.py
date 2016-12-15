# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.front.api.products import FrontProductViewSet


def populate_front_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shuup/front/products", FrontProductViewSet)
