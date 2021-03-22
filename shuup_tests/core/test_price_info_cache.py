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

from shuup.core.utils.price_cache import (
    cache_many_price_info,
    cache_price_info,
    get_cached_price_info,
    get_many_cached_price_info,
)
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_price_info_cache_bump(rf):
    initial_price = 10
    shop = factories.get_default_shop()
    tax = factories.get_default_tax()
    tax_class = factories.get_default_tax_class()
    product = factories.create_product(
        "product", shop=shop, supplier=factories.get_default_supplier(), default_price=initial_price
    )
    request = apply_request_middleware(rf.get("/"))

    def assert_cache_product():
        cache_price_info(request, product, 1, product.get_price_info(request))
        assert get_cached_price_info(request, product, 1).price == shop.create_price(initial_price)

    def assert_nothing_is_cached():
        # nothing is cached
        assert get_cached_price_info(request, product, 1) is None

    # cache the item
    assert_nothing_is_cached()
    assert_cache_product()

    # cache bumped - the cache should be dropped - then, cache again
    tax.save()
    assert_nothing_is_cached()
    assert_cache_product()

    # cache bumped - the cache should be dropped - then, cache again
    tax_class.save()
    assert_nothing_is_cached()
    assert_cache_product()

    # cache bumped - the cache should be dropped - then, cache again
    product.save()
    assert_nothing_is_cached()
    assert_cache_product()

    shop_product = product.get_shop_instance(shop)

    # cache bumped - the cache should be dropped - then, cache again
    shop_product.save()
    assert_nothing_is_cached()
    assert_cache_product()

    category = factories.get_default_category()

    # cache bumped - the cache should be dropped - then, cache again
    shop_product.categories.add(category)
    assert_nothing_is_cached()
    assert_cache_product()


@pytest.mark.django_db
def test_many_price_info_cache_bump(rf):
    initial_price = 10
    shop = factories.get_default_shop()
    tax = factories.get_default_tax()
    tax_class = factories.get_default_tax_class()
    product = factories.create_product(
        "product", shop=shop, supplier=factories.get_default_supplier(), default_price=initial_price
    )
    child1 = factories.create_product("child1", shop=shop, supplier=factories.get_default_supplier(), default_price=5)
    child2 = factories.create_product("child2", shop=shop, supplier=factories.get_default_supplier(), default_price=9)
    child1.link_to_parent(product, variables={"color": "red"})
    child2.link_to_parent(product, variables={"color": "blue"})

    request = apply_request_middleware(rf.get("/"))
    child1_pi = child1.get_price_info(request)
    child2_pi = child1.get_price_info(request)

    def assert_cache_products():
        cache_many_price_info(request, product, 1, [child1_pi, child2_pi])
        assert get_many_cached_price_info(request, product, 1)[0].price == child1_pi.price
        assert get_many_cached_price_info(request, product, 1)[1].price == child2_pi.price

    def assert_nothing_is_cached():
        # nothing is cached
        assert get_many_cached_price_info(request, product, 1) is None

    # cache the item
    assert_nothing_is_cached()
    assert_cache_products()

    # cache bumped - the cache should be dropped - then, cache again
    tax.save()
    assert_nothing_is_cached()
    assert_cache_products()

    # cache bumped - the cache should be dropped - then, cache again
    tax_class.save()
    assert_nothing_is_cached()
    assert_cache_products()

    # cache bumped - the cache should be dropped - then, cache again
    product.save()
    assert_nothing_is_cached()
    assert_cache_products()

    shop_product = product.get_shop_instance(shop)

    # cache bumped - the cache should be dropped - then, cache again
    shop_product.save()
    assert_nothing_is_cached()
    assert_cache_products()

    category = factories.get_default_category()

    # cache bumped - the cache should be dropped - then, cache again
    shop_product.categories.add(category)
    assert_nothing_is_cached()
    assert_cache_products()

    # cache bumped - the cache should be dropped - then, cache again
    supplier = shop_product.suppliers.first()
    supplier.enabled = False
    supplier.save()
    assert_nothing_is_cached()
    assert_cache_products()
