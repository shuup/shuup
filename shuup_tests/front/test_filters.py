# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from shuup.utils.django_compat import reverse

from shuup.core.models import Category
from shuup.front.utils.sorts_and_filters import set_configuration
from shuup.testing import factories
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_product_price_range_filter():
    shop = factories.get_default_shop()
    product = factories.get_default_product()
    category = factories.get_default_category()
    shop_product = product.get_shop_instance(shop)
    shop_product.default_price_value = 10
    shop_product.categories.add(category)
    shop_product.save()

    client = SmartClient()
    config = {
        "filter_products_by_price": True,
        "filter_products_by_price_range_min": 5,
        "filter_products_by_price_range_max": 15,
        "filter_products_by_price_range_size": 5
    }
    set_configuration(category=category, data=config)
    url = reverse('shuup:category', kwargs={'pk': category.pk, 'slug': category.slug})
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product.id)
    price_range_select = soup.find(id="id_price_range")
    # as the configuration is not set to override shop default configuration
    # this field shouldn't be there..
    assert price_range_select is None

    # make the category configuration override the shop's default config
    config.update({"override_default_configuration": True})
    set_configuration(category=category, data=config)
    url = reverse('shuup:category', kwargs={'pk': category.pk, 'slug': category.slug})
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product.id)
    price_range_select = soup.find(id="id_price_range")
    price_ranges = price_range_select.find_all("option")
    assert len(price_ranges) == 4

    # filter products with prices above $15
    filtered_url = "{}?price_range={}".format(url, price_ranges[-1].attrs["value"])
    response, soup = client.response_and_soup(filtered_url)
    assert response.status_code == 200
    assert not soup.find(id="product-%d" % product.id)

    # explicitly disable the override
    config.update({"override_default_configuration": False})
    set_configuration(category=category, data=config)
    url = reverse('shuup:category', kwargs={'pk': category.pk, 'slug': category.slug})
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product.id)
    price_range_select = soup.find(id="id_price_range")
    assert price_range_select is None


@pytest.mark.django_db
def test_category_filter():
    shop = factories.get_default_shop()

    category1 = Category.objects.create(name="Category 1")
    category1.shops.add(shop)
    product1 = factories.create_product("p1", shop, factories.get_default_supplier(), "10")
    shop_product1 = product1.get_shop_instance(shop)
    shop_product1.categories.add(category1)

    category2 = Category.objects.create(name="Category 2")
    category2.shops.add(shop)
    product2 = factories.create_product("p2", shop, factories.get_default_supplier(), "20")
    shop_product2 = product2.get_shop_instance(shop)
    shop_product2.categories.add(category2)

    client = SmartClient()
    config = {"filter_products_by_category": True}
    set_configuration(shop=shop, data=config)

    url = reverse('shuup:all-categories')

    # 1) go to all categories view and list products
    # no filters being applied should list all products
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)

    # 2) filter by category2 id only
    response, soup = client.response_and_soup("{}?categories={}".format(url, category2.pk))
    assert response.status_code == 200
    assert not soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)

    # 3) filter by category1 and category2 id
    response, soup = client.response_and_soup("{}?categories={},{}".format(url, category1.pk, category2.pk))
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)

    # 4) filter by blank value, it shouldn't break
    response, soup = client.response_and_soup("{}?categories=".format(url))
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)
