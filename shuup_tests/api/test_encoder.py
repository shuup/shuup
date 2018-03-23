# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import mock
import pytest
from rest_framework import renderers, serializers

from shuup.api.encoders import ExtJSONEncoder
from shuup.core.models import Order, ShopStatus
from shuup.testing import factories
from shuup.utils.money import Money


def test_encoder():
    encoder = ExtJSONEncoder()
    assert encoder.default(Money(10, "USD")) == 10
    assert encoder.default(ShopStatus.DISABLED) == ShopStatus.DISABLED.value


@pytest.mark.django_db
def test_money_field_serialize_real_world():
    shop = factories.get_default_shop()
    customer = factories.create_random_person("en")
    supplier = factories.get_default_supplier()
    product = factories.create_product("test", shop, supplier, "12.42")
    order = factories.create_random_order(customer, [product], 1, shop)

    class OrderSerializer(serializers.ModelSerializer):
        taxful_total_price = serializers.ReadOnlyField()

        class Meta:
            model = Order
            fields = ["taxful_total_price"]

    data = renderers.JSONRenderer().render(OrderSerializer(order).data).decode("utf-8")
    assert float(json.loads(data)["taxful_total_price"]) == float(order.taxful_total_price_value)

    # make sure it is being called
    with mock.patch("shuup.api.encoders.ExtJSONEncoder.default") as mocked_encoder:
        mocked_encoder.return_value = 1
        renderers.JSONRenderer().render(OrderSerializer(order).data)
    mocked_encoder.assert_called()
