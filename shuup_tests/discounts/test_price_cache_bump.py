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
from datetime import datetime, timedelta
from mock import patch

from shuup.core.utils.price_cache import cache_price_info, get_cached_price_info
from shuup.discounts.exceptions import DiscountM2MChangeError
from shuup.discounts.models import Discount, HappyHour, TimeRange
from shuup.discounts.signal_handlers import handle_generic_m2m_changed
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_bump_caches_signal(rf):
    """
    Test that prices are bumped when discount objects changes
    """
    initial_price = 10
    discounted_price = 5

    shop1 = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2", domain="shop2")

    product1 = factories.create_product(
        "product", shop=shop1, supplier=factories.get_default_supplier(), default_price=initial_price
    )

    product2 = factories.create_product(
        "product2", shop=shop2, supplier=factories.get_default_supplier(), default_price=20
    )

    now = datetime(2018, 1, 1, 9, 0, tzinfo=pytz.UTC)  # 01/01/2018 09:00 AM

    with patch("django.utils.timezone.now", new=lambda: now):
        discount = Discount.objects.create(
            name="discount",
            active=True,
            start_datetime=now - timedelta(days=10),
            end_datetime=now + timedelta(days=10),
            discounted_price_value=discounted_price,
            shop=shop1,
        )

        request = apply_request_middleware(rf.get("/"))
        request_shop2 = apply_request_middleware(rf.get("/", HTTP_HOST=shop2.domain))

        def assert_cache_product1(discounted=False):
            cache_price_info(request, product1, 1, product1.get_price_info(request))
            if discounted:
                assert get_cached_price_info(request, product1, 1).price == shop1.create_price(discounted_price)
            else:
                assert get_cached_price_info(request, product1, 1).price == shop1.create_price(initial_price)

        def assert_product1_is_not_cached():
            assert get_cached_price_info(request, product1) is None

        def assert_product2_is_cached():
            assert get_cached_price_info(request_shop2, product2) is not None

        assert_product1_is_not_cached()
        assert_cache_product1(True)

        # cache bumped - the cache should be dropped - then, cache again
        discount.save()
        assert_product1_is_not_cached()
        assert_cache_product1(True)

        # cache product 2.. from now on, shop2 cache should never be bumped
        cache_price_info(request_shop2, product2, 1, product2.get_price_info(request_shop2))
        assert_product2_is_cached()

        discount.product = product1
        discount.save()

        assert_product1_is_not_cached()
        assert_cache_product1(True)
        assert_product2_is_cached()

        happy_hour = HappyHour.objects.create(name="hh 1", shop=shop1)
        happy_hour.discounts.add(discount)
        assert_product1_is_not_cached()
        assert_cache_product1(True)
        assert_product2_is_cached()

        happy_hour.save()
        assert_product1_is_not_cached()
        assert_cache_product1(True)
        assert_product2_is_cached()

        time_range = TimeRange.objects.create(
            happy_hour=happy_hour,
            from_hour=(now - timedelta(hours=1)).time(),
            to_hour=(now + timedelta(hours=1)).time(),
            weekday=now.weekday(),
        )
        assert_product1_is_not_cached()
        assert_cache_product1(True)
        assert_product2_is_cached()

        time_range.save()
        assert_product1_is_not_cached()
        assert_cache_product1(True)
        assert_product2_is_cached()

        time_range.delete()
        assert_product1_is_not_cached()
        assert_cache_product1(True)
        assert_product2_is_cached()

        with pytest.raises(DiscountM2MChangeError):
            handle_generic_m2m_changed("test", time_range)
