# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal

import pytest
from django.core.urlresolvers import reverse

from shuup.front.themes.views._product_price import ProductPriceView
from shuup.testing.factories import (
    create_product, get_default_product, get_default_shop,
    get_default_supplier
)


@pytest.mark.django_db
def test_product_price(client):
    shop = get_default_shop()
    product = get_default_product()
    response = client.get(
        reverse('shuup:xtheme_extra_view', kwargs={
                'view': 'product_price'
            }
        ) + "?id=%s&quantity=%s" % (product.pk, 1)
    )
    assert response.context_data["product"] == product
    assert b"form" in response.content


@pytest.mark.django_db
def test_variation_product_price(client):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("Parent", supplier=supplier, shop=shop, default_price="10")
    child = create_product("SimpleVarChild", supplier=supplier, shop=shop, default_price="5")
    child.link_to_parent(product, variables={"size": "S"})
    response = client.get(
        reverse('shuup:xtheme_extra_view', kwargs={
                'view': 'product_price'
            }
        ) + "?id=%s&quantity=%s&var_1=1" % (product.pk, 1)
    )
    assert response.context_data["product"] == child
    assert b"form" in response.content

    sp = child.get_shop_instance(shop)
    sp.suppliers.remove(supplier)
    response = client.get(
        reverse('shuup:xtheme_extra_view', kwargs={
                'view': 'product_price'
            }
        ) + "?id=%s&quantity=%s&var_1=1" % (product.pk, 1)
    )
    assert response.context_data["product"] == child
    # product isn't orderable since no supplier
    assert b"no-price" in response.content


def test_product_price_get_quantity(rf):
    shop = get_default_shop()
    product = create_product("sku", shop=shop)
    shop_product = product.get_shop_instance(shop)

    view = ProductPriceView()
    view.request = rf.get('/')
    assert 'quantity' not in view.request.GET

    def check(shop_product, input_value, expected_output):
        view.request.GET = dict(view.request.GET, quantity=input_value)
        result = view._get_quantity(shop_product)
        if expected_output is None:
            assert result is None
        else:
            assert isinstance(result, Decimal)
            assert result == expected_output

    check(shop_product, '42', 42)
    check(shop_product, '1.5', Decimal('1.5'))
    check(shop_product, '3.2441', Decimal('3.2441'))
    check(shop_product, '0.0000000001', Decimal('0.0000000001'))
    check(shop_product, '0.000000000001', Decimal('0.000000000001'))
    check(shop_product, '123456789123456789123456789', 123456789123456789123456789)
    check(shop_product, '0', 0)
    check(shop_product, '-100', None)
    check(shop_product, '', None)
    check(shop_product, 'inf', None)
    check(shop_product, 'nan', None)
    check(shop_product, 'Hello', None)
    check(shop_product, '1.2.3', None)
    check(shop_product, '1.2.3.4', None)
    check(shop_product, '1-2', None)
    check(shop_product, '1 2 3', None)
    check(shop_product, '1e30', None)
    check(shop_product, '1,5', None)
    check(shop_product, 'mämmi', None)
    check(shop_product, '3€', None)
    check(shop_product, '\0', None)
    check(shop_product, '123\0', None)
    check(shop_product, '123\0456', None)
    check(shop_product, '\n', None)
