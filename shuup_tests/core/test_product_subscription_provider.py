# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal

from shuup.apps.provides import override_provides
from shuup.core.utils.product_subscription import ProductSubscriptionContext, get_product_subscription_options
from shuup.testing import factories


@pytest.mark.django_db
def test_product_subscription_provider():
    shop = factories.get_default_shop()
    user = factories.create_random_user()
    supplier = factories.get_default_supplier()
    product = factories.create_product("product", shop, supplier, 10)

    with override_provides(
        "product_subscription_option_provider",
        ["shuup.testing.subscription_option_provider.TestSubscriptionOptionProvider"],
    ):
        context = ProductSubscriptionContext(shop, product, supplier)
        plans = list(get_product_subscription_options(context))

        assert plans[0].label == "Monthly"
        assert plans[0].price.value == Decimal(9.9)
        assert plans[1].label == "Yearly"
        assert plans[1].price.value == Decimal(99)
