# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable

from shuup.core.utils.product_subscription import (
    BaseProductSubscriptionOptionProvider, ProductSubscriptionContext,
    ProductSubscriptionOption
)


class TestSubscriptionOptionProvider(BaseProductSubscriptionOptionProvider):
    @classmethod
    def get_subscription_options(cls, context: ProductSubscriptionContext) -> Iterable[ProductSubscriptionOption]:
        yield ProductSubscriptionOption(
            value="mo",
            label="Monthly",
            price=context.shop.create_price(9.90),
            description="A nice monthly plan.\nTrial period: 30 days"
        )
        yield ProductSubscriptionOption(
            value="yr",
            label="Yearly",
            price=context.shop.create_price(99),
            description="A nice yearly plan.\nTrial period: 30 days"
        )
