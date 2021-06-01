# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import Supplier, SupplierModule
from shuup.testing.factories import get_default_shop

IDENTIFIER = "test_simple_supplier"


def get_simple_supplier(stock_managed=True, shop=None):
    supplier = Supplier.objects.filter(identifier=IDENTIFIER).first()
    simple_supplier_module, _ = SupplierModule.objects.get_or_create(
        module_identifier="simple_supplier", defaults={"name": "Simple supplier"}
    )
    if not supplier:
        supplier = Supplier.objects.create(
            identifier=IDENTIFIER,
            name="Simple Supplier",
            stock_managed=stock_managed,
        )
    supplier.supplier_modules.add(simple_supplier_module)
    if not shop:
        shop = get_default_shop()
    supplier.shops.add(shop)
    return supplier
