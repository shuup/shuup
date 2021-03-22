# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.apps.provides import override_provides
from shuup.testing import factories
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_product_subscription_options():
    shop = factories.get_default_shop()
    user = factories.create_random_user()
    supplier = factories.get_default_supplier()
    product = factories.create_product("product", shop, supplier, 10)

    client = SmartClient()

    with override_provides(
        "product_subscription_option_provider",
        ["shuup.testing.subscription_option_provider.TestSubscriptionOptionProvider"],
    ):
        response = client.soup(reverse("shuup:product", kwargs=dict(pk=product.pk, slug=product.slug)))
        purchase_options = response.find("ul", {"class": "product-purchase-options-list-group"})

        # there is an option for one-time purchase
        one_time_purchase = purchase_options.find_all("li", {"class": "list-group-item"})[0]
        assert one_time_purchase.find("input", {"name": "purchase-option", "value": "one-time"})

        # there is an option for subscription purchase
        subscription = purchase_options.find_all("li", {"class": "list-group-item"})[1]
        assert subscription.find("input", {"name": "purchase-option", "value": "subscription"})
        # the subscription options should be yr and mo, according to the TestSubscriptionOptionProvider
        assert subscription.find_all("input", {"name": "subscription-option", "value": "mo"})
        assert subscription.find_all("input", {"name": "subscription-option", "value": "yr"})
