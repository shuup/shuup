# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.api.factories import viewset_factory
from shuup.customer_group_pricing.models import CgpPrice


def populate_customer_group_pricing_api(router):
    """
    :param router: Router
    :type router: rest_framework.routers.DefaultRouter
    """
    router.register("shuup/cgp_price", viewset_factory(CgpPrice))
