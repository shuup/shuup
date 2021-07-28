# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest
import random

from shuup.core.models import Supplier
from shuup.discounts.models import Discount
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_discounted_price(rf):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    request = rf.get("/")
    request.shop = shop
    apply_request_middleware(request)
    assert request.shop == shop

    original_price = 10
    product = factories.create_product("test1", shop=shop, supplier=supplier, default_price=original_price)
    shop_product = product.get_shop_instance(shop)

    # Set discount with discount amount for $2
    discount_amount = 2
    discount = Discount.objects.create(
        active=True, product=product, supplier=supplier, discount_amount_value=discount_amount, shop=shop
    )

    # Even though the supplier is matching with the product there is no discount
    # since the supplier is not in pricing context.
    assert not hasattr(request, "supplier")
    assert supplier in shop_product.suppliers.all()
    assert product.get_price_info(request).price == request.shop.create_price(10)

    setattr(request, "supplier", supplier)
    assert product.get_price_info(request).price == request.shop.create_price(8)

    # No discount once we change the discount supplier
    new_supplier = Supplier.objects.create(identifier="*")
    discount.supplier = new_supplier
    discount.save()
    assert product.get_price_info(request).price == request.shop.create_price(10)
