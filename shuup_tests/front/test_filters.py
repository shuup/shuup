# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.urlresolvers import reverse

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
    set_configuration(
        category=category,
        data={
            "filter_products_by_price": True,
            "filter_products_by_price_range_min": 5,
            "filter_products_by_price_range_max": 15,
            "filter_products_by_price_range_size": 5
        }
    )
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
