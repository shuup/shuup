# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import Counter
from decimal import Decimal

import pytest
from django.test import override_settings
from rest_framework import status

from shuup.core import cache
from shuup.core.models import Order, OrderStatusManager
from shuup.simple_supplier.module import SimpleSupplierModule
from shuup.testing import factories
from shuup.testing.basket_helpers import get_client, REQUIRED_SETTINGS
from shuup.utils.numbers import bankers_round


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
def test_basket_with_package_product(admin_user):
    with override_settings(**REQUIRED_SETTINGS):
        shop = factories.get_default_shop()
        factories.get_default_shipping_method()
        factories.get_default_payment_method()
        OrderStatusManager().ensure_default_statuses()

        client = get_client(admin_user)
        response = client.post("/api/shuup/basket/new/", format="json", data={"shop": shop.pk})
        assert response.status_code == status.HTTP_201_CREATED
        basket_uuid = response.data["uuid"]

        supplier = factories.get_supplier(SimpleSupplierModule.identifier, shop=shop, stock_managed=True)

        # base product - 1kg of sand
        base_sand_product = factories.create_product(
            "Sand",
            shop=shop,
            supplier=supplier,
            default_price="15.2",
            net_weight=Decimal(1)
        )

        # 10kg bag of sand - package made by 10kg of sand
        sand_bag_10kg_product = factories.create_product(
            "Sand-bag-10-kg",
            shop=shop,
            supplier=supplier,
            default_price="149.9",
            net_weight=Decimal(10000)
        )
        sand_bag_10kg_product.make_package({
            base_sand_product: 10
        })
        sand_bag_10kg_product.save()

        # 18.45kg bag of sand - package made by 18.45kg of sand
        sand_bag_1845kg_product = factories.create_product(
            "Sand-bag-1845-kg",
            shop=shop,
            supplier=supplier,
            default_price="179.9",
            net_weight=Decimal(18450)
        )
        sand_bag_1845kg_product.make_package({
            base_sand_product: 18.45
        })
        sand_bag_1845kg_product.save()

        # 25kg bag of sand - package made by 25kg of sand
        sand_bag_25kg_product = factories.create_product(
            "Sand-bag-25-kg",
            shop=shop,
            supplier=supplier,
            default_price="2450.25",
            net_weight=Decimal(25000)
        )
        sand_bag_25kg_product.make_package({
            base_sand_product: 25
        })
        sand_bag_25kg_product.save()

        initial_stock = 55

        # put 55 sands (55kg) in stock
        supplier.adjust_stock(base_sand_product.id, initial_stock)
        stock_status = supplier.get_stock_status(base_sand_product.id)
        assert stock_status.physical_count == initial_stock
        assert stock_status.logical_count == initial_stock

        # zero stock for packages
        assert supplier.get_stock_status(sand_bag_10kg_product.id).logical_count == 0
        assert supplier.get_stock_status(sand_bag_1845kg_product.id).logical_count == 0
        assert supplier.get_stock_status(sand_bag_25kg_product.id).logical_count == 0

        # add all the 3 packages to the basket, this will require (10 + 18.45 + 25 = 53.45 Sands)
        for product in [sand_bag_10kg_product, sand_bag_1845kg_product, sand_bag_25kg_product]:
            response = client.post("/api/shuup/basket/{}/add/".format(basket_uuid), format="json", data={
                "shop": shop.pk,
                "product": product.id
            })
            assert response.status_code == status.HTTP_200_OK

        # get the basket
        response = client.get("/api/shuup/basket/{}/".format(basket_uuid))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["validation_errors"] == []

        # now add more 25kg and it shouldn't have enough stock
        response = client.post("/api/shuup/basket/{}/add/".format(basket_uuid), format="json", data={
            "shop": shop.pk,
            "product": sand_bag_25kg_product.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient stock" in response.data["error"]

        # create order anyway
        response = client.post("/api/shuup/basket/{}/create_order/".format(basket_uuid), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        order = Order.objects.get(id=response.data["id"])
        line_counter = Counter()

        for line in order.lines.products():
            line_counter[line.product.id] += line.quantity

        assert bankers_round(line_counter[base_sand_product.id]) == bankers_round(
            Decimal(10) + Decimal(18.45) + Decimal(25)
        )
        assert line_counter[sand_bag_10kg_product.id] == 1
        assert line_counter[sand_bag_1845kg_product.id] == 1
        assert line_counter[sand_bag_25kg_product.id] == 1
