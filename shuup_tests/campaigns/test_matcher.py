# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.apps.provides import override_provides
from shuup.campaigns.utils.matcher import ProductCampaignMatcher, get_matching_for_product
from shuup.core.models import Category
from shuup.testing.factories import create_product, create_random_person, get_default_shop
from shuup.testing.models import UltraFilter


@pytest.mark.django_db
def test_ultrafilter():
    shop = get_default_shop()
    product = create_product("test", shop, default_price=20)
    shop_product = product.get_shop_instance(shop)
    product2 = create_product("test2", shop, default_price=2)
    category = Category.objects.create(name="test")

    matcher = ProductCampaignMatcher(shop_product)
    # test products
    uf = UltraFilter.objects.create()

    assert not matcher.matches(uf)
    uf.products.add(product)
    assert matcher.matches(uf)
    uf.products.remove(product)
    assert not matcher.matches(uf)
    uf.product = product
    uf.save()
    assert matcher.matches(uf)
    uf.product = None
    uf.save()

    # test shop_products
    assert not matcher.matches(uf)
    uf.shop_products.add(shop_product)
    assert matcher.matches(uf)
    uf.shop_products.remove(shop_product)
    assert not matcher.matches(uf)
    uf.shop_product = shop_product
    uf.save()
    assert matcher.matches(uf)
    uf.shop_product = None
    uf.save()

    # test category
    assert not matcher.matches(uf)
    uf.categories.add(category)
    shop_product.primary_category = category
    assert matcher.matches(uf)
    shop_product.primary_category = None
    assert not matcher.matches(uf)
    shop_product.categories.add(category)
    assert matcher.matches(uf)
    uf.categories.remove(category)

    assert not matcher.matches(uf)
    shop_product.categories.add(category)
    uf.category = category
    uf.save()
    assert matcher.matches(uf)
    shop_product.categories.remove(category)
    shop_product.primary_category = None
    shop_product.save()
    assert not matcher.matches(uf)
    shop_product.primary_category = category
    assert matcher.matches(uf)
    uf.category = None
    uf.save()

    # test product_type
    assert not matcher.matches(uf)
    uf.product_types.add(product.type)
    assert matcher.matches(uf)
    uf.product_types.remove(product.type)
    assert not matcher.matches(uf)
    uf.product_type = product.type
    uf.save()
    assert matcher.matches(uf)
    uf.product_type = None
    uf.save()

    # test unsupported type
    contact = create_random_person()
    assert not matcher.matches(uf)
    uf.contact = contact
    uf.save()
    assert not matcher.matches(uf)


@pytest.mark.django_db
def test_provides():
    shop = get_default_shop()
    product = create_product("test", shop, default_price=20)
    shop_product = product.get_shop_instance(shop)

    with override_provides("campaign_catalog_filter", [__name__ + ":UltraFilter"]):
        uf = UltraFilter.objects.create()
        uf.products.add(product)
        assert get_matching_for_product(shop_product, provide_category="campaign_catalog_filter")
        assert not get_matching_for_product(shop_product, provide_category="test_test_test")
