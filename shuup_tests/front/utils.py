# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import StockBehavior
from shuup.testing.factories import create_package_product


def get_unstocked_package_product_and_stocked_child(shop, supplier, child_logical_quantity=1):
    package_product = create_package_product("Package-Product-Test", shop=shop, supplier=supplier, children=1)
    assert package_product.stock_behavior == StockBehavior.UNSTOCKED

    quantity_map = package_product.get_package_child_to_quantity_map()
    assert len(quantity_map.keys()) == 1

    child_product = list(quantity_map.keys())[0]
    child_product.stock_behavior = StockBehavior.STOCKED
    child_product.save()

    assert quantity_map[child_product] == 1

    supplier.adjust_stock(child_product.id, child_logical_quantity)

    stock_status = supplier.get_stock_status(child_product.id)
    assert stock_status.logical_count == child_logical_quantity

    return package_product, child_product
