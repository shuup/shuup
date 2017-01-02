# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.urlresolvers import reverse

from shuup.testing.factories import create_product, get_default_product, get_default_shop, get_default_supplier


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
