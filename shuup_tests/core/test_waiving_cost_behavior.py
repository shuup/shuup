# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest

from shuup.core.models import OrderLineType, WaivingCostBehaviorComponent
from shuup.testing.factories import (
    create_product,
    get_default_shipping_method,
    get_default_supplier,
    get_shop,
    get_supplier,
)

from .test_order_creator import seed_source


@pytest.mark.django_db
def test_single_supplier(admin_user):
    shipping_method = get_default_shipping_method()
    component = WaivingCostBehaviorComponent.objects.create(
        price_value=decimal.Decimal(8),
        waive_limit_value=decimal.Decimal(10),
    )
    shipping_method.behavior_components.add(component)

    source = seed_source(admin_user)
    product = create_product(sku="sup1", shop=source.shop, supplier=get_default_supplier(), default_price=5)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(),
        base_unit_price=source.create_price(5),
    )
    source.shipping_method = shipping_method

    # there not waiving costs as the total is below 10
    costs = list(shipping_method.get_costs(source))
    assert costs[0].price.value == decimal.Decimal(8)

    # add more items
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(),
        quantity=3,
        base_unit_price=source.create_price(5),
    )

    # now that the total is greater than 10, there is no cost
    costs = list(shipping_method.get_costs(source))
    assert costs[0].price.value == decimal.Decimal(0)


@pytest.mark.django_db
def test_different_suppliers(admin_user):
    supplier_1 = get_supplier("simple_supplier", name="Supplier 1", shop=get_shop())
    supplier_2 = get_supplier("simple_supplier", name="Supplier 2", shop=get_shop())

    # this service will only be available for supplier_2
    shipping_method = get_default_shipping_method()
    shipping_method.supplier = supplier_2
    shipping_method.save()
    component = WaivingCostBehaviorComponent.objects.create(
        price_value=decimal.Decimal(10),
        waive_limit_value=decimal.Decimal(20),
    )
    shipping_method.behavior_components.add(component)

    source = seed_source(admin_user)
    product_1 = create_product(sku="sup1", shop=source.shop, supplier=supplier_1, default_price=25)
    product_2 = create_product(sku="sup2", shop=source.shop, supplier=supplier_2, default_price=4)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product_1,
        supplier=supplier_1,
        base_unit_price=source.create_price(25),
    )
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product_2,
        supplier=supplier_2,
        base_unit_price=source.create_price(4),
    )
    source.shipping_method = shipping_method

    # there not waiving costs as the total is below 20 for supplier_2
    costs = list(shipping_method.get_costs(source))
    assert costs[0].price.value == decimal.Decimal(10)

    # add more items of supplier_2
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product_2,
        supplier=supplier_2,
        quantity=10,
        base_unit_price=source.create_price(4),
    )

    # now that the total is greater than 20, there is no cost
    costs = list(shipping_method.get_costs(source))
    assert costs[0].price.value == decimal.Decimal(0)
