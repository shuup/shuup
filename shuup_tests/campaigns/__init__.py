# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import activate

from shuup.testing.factories import create_random_person, get_default_customer_group, get_payment_method, get_shop
from shuup.testing.utils import apply_request_middleware


def initialize_test(rf, include_tax=False):
    activate("en")
    shop = get_shop(prices_include_tax=include_tax)
    shop.domain = "campaign"
    shop.save()

    # Valid baskets needs some payment methods to be available
    get_payment_method(shop)
    # Since some of the baskets are created for the default shop:
    get_payment_method(None)

    group = get_default_customer_group()
    customer = create_random_person()
    customer.groups.add(group)
    customer.save()

    request = rf.get("/")
    request.shop = shop
    request.META["HTTP_HOST"] = "campaign.shuup.com"
    apply_request_middleware(request)
    request.customer = customer
    return request, shop, group
