# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal

import pytest

from shuup.core.models import RoundingMode, RoundingBehaviorComponent
from shuup.core.order_creator import OrderSource
from shuup.testing.factories import get_default_shop
from shuup_tests.utils.fixtures import regular_user

regular_user = regular_user  # noqa


@pytest.mark.django_db
@pytest.mark.parametrize('price, cost, mode', [
    ('2.32', '-0.02', RoundingMode.ROUND_DOWN),
    ('2.35', '0.00', RoundingMode.ROUND_DOWN),
    ('2.38', '-0.03', RoundingMode.ROUND_DOWN),
    ('2.32', '0.03', RoundingMode.ROUND_UP),
    ('2.35', '0.00', RoundingMode.ROUND_UP),
    ('2.38', '0.02', RoundingMode.ROUND_UP),
    ('2.32', '-0.02', RoundingMode.ROUND_HALF_DOWN),
    ('2.35', '0.00', RoundingMode.ROUND_HALF_DOWN),
    ('2.38', '0.02', RoundingMode.ROUND_HALF_DOWN),
    ('2.32', '-0.02', RoundingMode.ROUND_HALF_UP),
    ('2.35', '0.00', RoundingMode.ROUND_HALF_UP),
    ('2.38', '0.02', RoundingMode.ROUND_HALF_UP)
])
def test_rounding_costs(price, cost, mode):
    shop = get_default_shop()
    source = OrderSource(shop)
    source.total_price_of_products = source.create_price(price)
    behavior = RoundingBehaviorComponent.objects.create(mode=mode)
    costs = list(behavior.get_costs(None, source))

    assert len(costs) == 1
    assert costs[0].price.value == Decimal(cost)

