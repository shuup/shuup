# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shoop.testing.factories import (
    get_default_product, get_default_shop_product, get_default_supplier
)


@pytest.mark.django_db
def test_default_supplier(rf):
    supplier = get_default_supplier()
    shop_product = get_default_shop_product()
    product = shop_product.product
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 0
    assert not list(supplier.get_orderability_errors(shop_product, 1, customer=None))
