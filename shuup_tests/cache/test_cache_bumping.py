# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Tests for utils.price_display and the price filters.
"""
import pytest
import pytz
from datetime import datetime
from mock import patch

from shuup.core.models import get_person_contact
from shuup.core.utils import context_cache
from shuup.testing import factories


@pytest.mark.django_db
def test_bump_caches_signal(rf):
    """
    Test that caches are actually bumped also when calling bump function with id's
    """

    initial_price = 10

    shop1 = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2", domain="shop2")

    now = datetime(2018, 1, 1, 9, 0, tzinfo=pytz.UTC)  # 01/01/2018 09:00 AM

    def assert_cache_bumped(prods):
        for sp in prods:
            key, val = context_cache.get_cached_value(
                identifier="is_orderable",
                item=sp,
                context={"customer": contact},
                supplier=factories.get_default_supplier(),
                stock_managed=bool(factories.get_default_supplier() and factories.get_default_supplier().stock_managed),
                quantity=1,
                allow_cache=True,
            )

            assert val is None

    with patch("django.utils.timezone.now", new=lambda: now):
        product1 = factories.create_product(
            "product", shop=shop1, supplier=factories.get_default_supplier(), default_price=initial_price
        )

        product2 = factories.create_product(
            "product2", shop=shop2, supplier=factories.get_default_supplier(), default_price=20
        )

        user = factories.create_random_user()
        contact = get_person_contact(user)

        shop_product1 = product1.shop_products.filter(shop=shop1).first()
        shop_product2 = product2.shop_products.filter(shop=shop2).first()

        assert shop_product1.is_orderable(factories.get_default_supplier(shop1), contact, 1) is True
        assert shop_product2.is_orderable(factories.get_default_supplier(shop2), contact, 1) is True

        # Test single product id bumping
        context_cache.bump_cache_for_product(product2.id, shop=shop2)
        context_cache.bump_cache_for_product(product1.id, shop=shop1)
        assert_cache_bumped([shop_product1, shop_product2])

        # Test list bumping
        context_cache.bump_cache_for_product([product2.id], shop=shop2)
        context_cache.bump_cache_for_product([product1.id], shop=shop1)
        assert_cache_bumped([shop_product1, shop_product2])
