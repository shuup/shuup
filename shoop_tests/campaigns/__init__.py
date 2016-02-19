# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import activate
from shoop.testing.factories import (
    get_shop, get_default_customer_group, get_default_payment_method,
    create_random_person
)
from shoop.testing.utils import apply_request_middleware


def initialize_test(rf, include_tax=False):
    activate("en")
    shop = get_shop(prices_include_tax=include_tax)
    get_default_payment_method()  # Valid baskets needs some payment methods to be available

    group = get_default_customer_group()
    customer = create_random_person()
    customer.groups.add(group)
    customer.save()

    request = rf.get("/")
    request.shop = shop
    apply_request_middleware(request)
    request.customer = customer
    return request, shop, group
