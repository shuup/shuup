# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_text
from django.utils.translation import activate, get_language

from shuup.core.models import DefaultOrderStatus, OrderLineType, OrderStatus, OrderStatusManager, OrderStatusRole
from shuup.core.order_creator import OrderCreator
from shuup.testing.factories import create_default_order_statuses, get_default_product, get_default_supplier
from shuup_tests.core.test_order_creator import seed_source


@pytest.mark.django_db
def test_order_statuses_are_translatable():
    create_default_order_statuses()
    assert OrderStatus.objects.translated(get_language()).count() == OrderStatus.objects.count()


@pytest.mark.django_db
def test_single_default_status_for_role():
    create_default_order_statuses()
    new_default_cancel = OrderStatus.objects.create(
        identifier="foo", role=OrderStatusRole.CANCELED, name="foo", default=True
    )
    assert new_default_cancel.default
    assert OrderStatus.objects.get_default_canceled() == new_default_cancel
    new_default_cancel.delete()

    # We can use this weird moment to cover the "no default" case, yay
    with pytest.raises(ObjectDoesNotExist):
        OrderStatus.objects.get_default_canceled()

    old_cancel = OrderStatus.objects.get(identifier=DefaultOrderStatus.CANCELED.value)
    assert not old_cancel.default  # This will have been reset when another status became the default
    old_cancel.default = True
    old_cancel.save()


@pytest.mark.django_db
def test_order_statuses(admin_user):
    create_default_order_statuses()

    source = seed_source(admin_user)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )

    creator = OrderCreator()
    order = creator.create_order(source)
    # new order, status/role is new/initial
    assert order.status.identifier == DefaultOrderStatus.INITIAL.value
    assert order.status.role == OrderStatusRole.INITIAL

    # FUTURE: order gets payment the status changes to processing/processing
    total = order.taxful_total_price.amount
    order.create_payment(total)

    assert order.status.identifier == DefaultOrderStatus.INITIAL.value
    assert order.status.role == OrderStatusRole.INITIAL

    # FUTURE: order is fully shipped the status changes to complete/complete
    order.create_shipment_of_all_products()
    assert order.status.identifier == DefaultOrderStatus.INITIAL.value
    assert order.status.role == OrderStatusRole.INITIAL


@pytest.mark.django_db
def test_order_status_manager():
    activate("en")
    OrderStatusManager().ensure_default_statuses()
    original_name = force_text(DefaultOrderStatus.INITIAL.label)
    new_name = "New name"
    status = OrderStatus.objects.get(identifier=DefaultOrderStatus.INITIAL.value)
    assert force_text(status.name) == original_name

    status.name = new_name
    status.save()
    assert force_text(status.name) == new_name
    OrderStatusManager().ensure_default_statuses()

    status = OrderStatus.objects.get(identifier=DefaultOrderStatus.INITIAL.value)
    assert force_text(status.name) == new_name
    old_identifier = status.identifier
    status.identifier = "random_identifier"
    status.save()
    OrderStatusManager().ensure_default_statuses()
    status = OrderStatus.objects.get(identifier=old_identifier)

    assert OrderStatus.objects.get_default_initial()
    assert OrderStatus.objects.get_default_processing()
    assert OrderStatus.objects.get_default_complete()
    assert OrderStatus.objects.get_default_canceled()
