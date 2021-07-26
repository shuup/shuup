# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from django.template import loader
from django.test.client import Client
from django.urls import reverse
from django.utils.encoding import force_text

from shuup.admin.modules.orders.sections import OrderHistorySection
from shuup.core.models import OrderStatus, OrderStatusHistory, ShipmentStatus, ShippingMode
from shuup.testing.factories import (
    add_product_to_order,
    create_empty_order,
    create_product,
    create_random_user,
    get_default_permission_group,
    get_default_shop,
    get_supplier,
)
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_order_shipments(rf, admin_user):
    shop = get_default_shop()
    supplier = get_supplier(module_identifier="simple_supplier", identifier="1", name="supplier")
    supplier.shops.add(shop)

    product = create_product("sku1", shop=shop, default_price=10)
    shop_product = product.get_shop_instance(shop=shop)
    shop_product.suppliers.set([supplier])

    product_quantities = {
        supplier.pk: {product.pk: 20},
    }

    def get_quantity(supplier, product):
        return product_quantities[supplier.pk][product.pk]

    order = create_empty_order(shop=shop)
    order.full_clean()
    order.save()
    order.change_status(OrderStatus.objects.get_default_processing())

    # Let's test the order order status history section for superuser
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)

    # Add product to order for supplier
    add_product_to_order(order, supplier, product, get_quantity(supplier, product), 8)

    context = OrderHistorySection.get_context_data(order, request)
    assert len(context) == 2

    # Let's create staff user without any permissions
    staff_user = create_random_user(is_staff=True)
    group = get_default_permission_group()
    staff_user.groups.add(group)
    shop.staff_members.add(staff_user)
    request = apply_request_middleware(rf.get("/"), user=staff_user, shop=shop)
    context = OrderHistorySection.get_context_data(order, request)
    assert len(context) == 2

    # works fine while rendering
    rendered_content = loader.render_to_string(
        OrderHistorySection.template,
        context={
            OrderHistorySection.identifier: context,
            "order_status_history": OrderStatusHistory.objects.filter(order=order).order_by("-created_on"),
        },
    )

    assert force_text(OrderStatus.objects.get_default_initial().name) in rendered_content
    assert force_text(OrderStatus.objects.get_default_processing().name) in rendered_content

    client = Client()
    client.force_login(admin_user)

    # We should see the order status section
    assert OrderHistorySection.visible_for_object(order, request)
