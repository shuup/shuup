# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from collections import defaultdict

import pytest
import six

from shuup.admin.modules.orders.sections import ShipmentSection
from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.core.models import ShippingMode, Supplier
from shuup.testing.factories import (
    add_product_to_order, create_empty_order, create_product,
    create_random_user, get_default_permission_group, get_default_shop
)
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_order_shipment_section(rf, admin_user):
    shop = get_default_shop()
    supplier1 = Supplier.objects.create(identifier="1", name="supplier1")
    supplier1.shops.add(shop)
    supplier2 = Supplier.objects.create(identifier="2")
    supplier2.shops.add(shop)

    product1 = create_product("sku1", shop=shop, default_price=10)
    shop_product1 = product1.get_shop_instance(shop=shop)
    shop_product1.suppliers.set([supplier1])

    product2 = create_product("sku3", shop=shop, default_price=10, shipping_mode=ShippingMode.NOT_SHIPPED)
    shop_product2 = product1.get_shop_instance(shop=shop)
    shop_product2.suppliers.set([supplier2])

    product_quantities = {
        supplier1.pk: {
            product1.pk: 20
        },
        supplier2.pk: {
            product2.pk: 10
        }
    }

    def get_quantity(supplier, product):
        return product_quantities[supplier.pk][product.pk]

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()

    # Let's test the order shipment section for superuser
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)

    # Add product 3 to order for supplier 2
    add_product_to_order(order, supplier2, product2, get_quantity(supplier2, product2), 8)

    # Product is not shippable so order section should not be available
    assert not ShipmentSection.visible_for_object(order, request)

    # Add product 2 to order for supplier 1
    add_product_to_order(order, supplier1, product1, get_quantity(supplier1, product1), 7)

    # Now we should see the shipment section
    assert ShipmentSection.visible_for_object(order, request)

    # Make order fully paid so we can start creting shipments and refunds
    order.cache_prices()
    order.check_all_verified()
    order.create_payment(order.taxful_total_price)
    assert order.is_paid()

    product_summary = order.get_product_summary()
    assert product_summary[product1.pk]["unshipped"] == 20
    assert product_summary[product2.pk]["unshipped"] == 0
    assert product_summary[product2.pk]["ordered"] == 10

    # Fully ship the order
    order.create_shipment({product1: 5}, supplier=supplier1)
    order.create_shipment({product1: 5}, supplier=supplier1)
    order.create_shipment({product1: 10}, supplier=supplier1)

    assert not order.get_unshipped_products()
    assert order.is_fully_shipped()

    context = ShipmentSection.get_context_data(order, request)
    assert len(context["suppliers"]) == 2
    assert len(context["create_urls"].keys()) == 2  # One for each supplier
    assert len(context["delete_urls"].keys()) == 3  # One for each shipment

    # Let's create staff user without any permissions
    staff_user = create_random_user(is_staff=True)
    group = get_default_permission_group()
    staff_user.groups.add(group)
    shop.staff_members.add(staff_user)
    request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop)
    context = ShipmentSection.get_context_data(order, request)
    assert len(context["suppliers"]) == 2
    assert len(context["create_urls"].keys()) == 0
    assert len(context["delete_urls"].keys()) == 0

    set_permissions_for_group(group, ["order.create-shipment"])
    request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop)
    context = ShipmentSection.get_context_data(order, request)
    assert len(context["suppliers"]) == 2
    assert len(context["create_urls"].keys()) == 2
    assert len(context["delete_urls"].keys()) == 0

    set_permissions_for_group(group, ["order.create-shipment", "order.delete-shipment"])
    request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop)
    context = ShipmentSection.get_context_data(order, request)
    assert len(context["suppliers"]) == 2
    assert len(context["create_urls"].keys()) == 2
    assert len(context["delete_urls"].keys()) == 3

    # Make product1 unshipped
    product1.shipping_mode = ShippingMode.NOT_SHIPPED
    product1.save()

    # We still should see the order shipment section since existing shipments
    assert ShipmentSection.visible_for_object(order, request)

    # Let's delete all shipments since both products is unshipped and we
    # don't need those.
    for shipment in order.shipments.all():
        shipment.soft_delete()
    
    assert not ShipmentSection.visible_for_object(order, request)
