# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import pytest

from shuup.core.models import Supplier
from shuup.simple_supplier.models import StockCount
from shuup.simple_supplier.utils import get_stock_adjustment_div
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.importing import load
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
@pytest.mark.parametrize("stock_managed", [True, False])
def test_get_stock_adjustment_div(rf, admin_user, stock_managed):
    shop = factories.get_default_shop()
    supplier = Supplier.objects.create(module_identifier="simple_supplier", stock_managed=stock_managed)
    supplier.shops.add(shop)

    product1 = factories.create_product(sku="test", shop=shop)
    shop_product = product1.get_shop_instance(shop)
    shop_product.suppliers.add(supplier)  # Stock is now created on div render

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    assert request.user == admin_user

    if stock_managed:
        assert supplier.stock_managed
        assert "Disable stock management" in get_stock_adjustment_div(request, supplier, product1)
    else:
        assert not supplier.stock_managed
        assert "Enable stock management" in get_stock_adjustment_div(request, supplier, product1)

    assert StockCount.objects.count() == 1
    product2 = factories.create_product(sku="test1", shop=shop, supplier=supplier)
    assert StockCount.objects.count() == 2

    if stock_managed:
        assert supplier.stock_managed
        assert "Disable stock management" in get_stock_adjustment_div(request, supplier, product2)
    else:
        assert not supplier.stock_managed
        assert "Enable stock management" in get_stock_adjustment_div(request, supplier, product2)
