# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.front.basket import get_basket
from shoop.simple_pricing.models import SimpleProductPrice
from shoop.testing.factories import get_default_shop
from shoop.testing.factories import get_default_product
from shoop.testing.factories import get_default_supplier


@pytest.mark.django_db
def test_basket(rf):
    shop = get_default_shop()
    product = get_default_product()
    supplier = get_default_supplier()
    request = rf.get("/")
    request.session = {}
    request.shop = shop
    basket = get_basket(request)
    assert basket == request.basket
    SimpleProductPrice.objects.get_or_create(shop=shop, product=product, defaults={"price": 50, "includes_tax": False})
    line = basket.add_product(supplier=supplier, shop=shop, product=product, quantity=10)
    assert line.quantity == 10
    assert basket.get_lines()
    assert basket.get_product_ids_and_quantities().get(product.pk) == 10
    delattr(request, "basket")
    basket = get_basket(request)
    assert basket.get_product_ids_and_quantities().get(product.pk) == 10
