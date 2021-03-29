# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import Shop


def get_shop_from_host(host):
    """
    Try to find a shop that matches a `host`
    e.g: shop.domain.com, domain.com, localhost:8000

    :type host str
    """
    shop = Shop.objects.filter(domain=host).first()

    if not shop and ":" in host:
        shop = Shop.objects.filter(domain=host.rsplit(":")[0]).first()

    if not shop:
        subdomain = host.split(".")[0]
        shop = Shop.objects.filter(domain=subdomain).first()

    return shop
