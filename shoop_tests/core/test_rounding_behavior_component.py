# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from decimal import Decimal

import pytest

from shoop.core.models import RoundingMode, RoundingBehaviorComponent
from shoop.core.order_creator import OrderSource
from shoop.testing.factories import get_default_shop
from shoop_tests.utils.fixtures import regular_user

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


@pytest.mark.django_db
def test_unavailability_reasons(admin_user, regular_user):
    shop = get_default_shop()
    source = OrderSource(shop)
    source.creator = admin_user
    behavior = RoundingBehaviorComponent.objects.create()
    reasons = list(behavior.get_unavailability_reasons(None, source))

    assert len(reasons) == 0

    source.creator = regular_user
    reasons = list(behavior.get_unavailability_reasons(None, source))

    assert len(reasons) == 1
