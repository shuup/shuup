# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import mock
import pytest
import pytz
from datetime import datetime

from shuup.core.models import OrderStatus, OrderStatusManager
from shuup.front.notify_events import ShipmentCreated, ShipmentDeleted, ShipmentSent
from shuup.notify.models import Script
from shuup.testing import factories
from shuup.utils.i18n import get_locally_formatted_datetime


@pytest.mark.django_db
def test_class_refunded():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier(shop)
    customer = factories.create_random_person("en")
    OrderStatusManager().ensure_default_statuses()

    product = factories.create_product("p", shop, supplier, 1.0)
    order = factories.create_order_with_product(product, supplier, 1, 1, shop=shop)

    # make sure to have some script enabled
    Script.objects.create(shop=shop, event_identifier="order_status_changed", name="Script", enabled=True)

    def get_mocked_cls():
        return mock.MagicMock(identifier="order_status_changed")

    with mock.patch("shuup.front.notify_events.OrderStatusChanged", new_callable=get_mocked_cls) as mocked:
        order.change_status(next_status=OrderStatus.objects.get_default_processing(), user=customer.user)
        mocked.assert_called()
        order.refresh_from_db()
        assert mocked.call_args[1]["order"] == order
        assert mocked.call_args[1]["old_status"] == OrderStatus.objects.get_default_initial()
        assert mocked.call_args[1]["new_status"] == OrderStatus.objects.get_default_processing()
        assert order.status == OrderStatus.objects.get_default_processing()

    # nothing changes
    with mock.patch("shuup.front.notify_events.OrderStatusChanged", new_callable=get_mocked_cls) as mocked:
        order.change_status(next_status=OrderStatus.objects.get_default_processing(), user=customer.user)
        mocked.assert_not_called()


@pytest.mark.django_db
def test_shipment_events():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier(shop)
    customer = factories.create_random_person("en")
    OrderStatusManager().ensure_default_statuses()

    product = factories.create_product("p", shop, supplier, 1.0)
    order = factories.create_order_with_product(product, supplier, 1, 1, shop=shop)

    Script.objects.create(shop=shop, event_identifier=ShipmentCreated.identifier, name="Script 1", enabled=True)
    Script.objects.create(shop=shop, event_identifier=ShipmentDeleted.identifier, name="Script 2", enabled=True)
    Script.objects.create(shop=shop, event_identifier=ShipmentSent.identifier, name="Script 3", enabled=True)

    def get_created_mocked_cls():
        return mock.MagicMock(identifier=ShipmentCreated.identifier)

    def get_sent_mocked_cls():
        return mock.MagicMock(identifier=ShipmentSent.identifier)

    def get_soft_mocked_cls():
        return mock.MagicMock(identifier=ShipmentDeleted.identifier)

    with mock.patch("shuup.front.notify_events.ShipmentCreated", new_callable=get_created_mocked_cls) as mocked1:
        shipment = order.create_shipment({product: 1}, supplier=supplier)
        mocked1.assert_called()

    with mock.patch("shuup.front.notify_events.ShipmentSent", new_callable=get_sent_mocked_cls) as mocked2:
        shipment.set_sent()
        mocked2.assert_called()

    with mock.patch("shuup.front.notify_events.ShipmentDeleted", new_callable=get_soft_mocked_cls) as mocked3:
        shipment.soft_delete()
        mocked3.assert_called()
