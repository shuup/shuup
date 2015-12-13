# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from django.test import RequestFactory

from shoop.core.models import (
    AnonymousContact, OrderLineType, ProductMode, Shop
)
from shoop.core.order_creator import OrderCreator, SourceLine
from shoop.testing.factories import (
    create_product, get_default_shop, get_default_supplier,
    get_initial_order_status
)
from shoop.testing.utils import apply_request_middleware
from shoop_tests.utils.basketish_order_source import BasketishOrderSource


@pytest.mark.django_db
def test_package():
    shop = get_default_shop()
    supplier = get_default_supplier()
    package_product = create_product("PackageParent", shop=shop, supplier=supplier)
    assert not package_product.get_package_child_to_quantity_map()
    children = [create_product("PackageChild-%d" % x, shop=shop, supplier=supplier) for x in range(4)]
    package_def = {child: 1 + i for (i, child) in enumerate(children)}
    package_product.make_package(package_def)
    assert package_product.is_package_parent()
    package_product.save()
    sp = package_product.get_shop_instance(shop)
    assert not list(sp.get_orderability_errors(supplier=supplier, quantity=1, customer=AnonymousContact()))

    with pytest.raises(ValueError):  # Test re-packaging fails
        package_product.make_package(package_def)

    # Check that OrderCreator can deal with packages

    source = BasketishOrderSource(get_default_shop())
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=package_product,
        supplier=get_default_supplier(),
        quantity=10,
        base_unit_price=source.create_price(10),
    )

    source.status = get_initial_order_status()

    request = apply_request_middleware(RequestFactory().get("/"))

    creator = OrderCreator(request)
    order = creator.create_order(source)
    pids_to_quantities = order.get_product_ids_and_quantities()
    for child, quantity in six.iteritems(package_def):
        assert pids_to_quantities[child.pk] == 10 * quantity
