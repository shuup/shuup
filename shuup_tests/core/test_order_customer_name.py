# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.testing.factories import create_empty_order, create_random_company, create_random_person


@pytest.mark.django_db
def test_order_customer_name_from_billing_address():
    person = create_random_person()
    order = create_empty_order()
    order.orderer = person
    order.save()
    order.refresh_from_db()
    assert order.customer_id is None
    assert order.orderer_id is not None
    assert order.get_customer_name() == order.billing_address.name
    assert order.shipping_address_id is not None


@pytest.mark.django_db
def test_order_customer_name_from_shipping_address():
    order = create_empty_order()
    assert order.customer_id is None
    assert order.orderer_id is None
    order.billing_address = None
    order.save()
    order.refresh_from_db()
    assert order.get_customer_name() == order.shipping_address.name


@pytest.mark.django_db
def test_order_customer_name_from_orderer():
    person = create_random_person()
    order = create_empty_order()
    order.orderer = person
    order.billing_address = None
    order.save()
    order.refresh_from_db()

    assert order.customer_id is None
    assert order.billing_address_id is None
    assert order.get_customer_name() == order.orderer.name
    assert order.shipping_address_id is not None


@pytest.mark.django_db
def test_order_customer_name_from_customer():
    company = create_random_company()
    person = create_random_person()
    order = create_empty_order()
    order.customer = company
    order.orderer = person
    order.save()
    order.refresh_from_db()
    assert order.shipping_address_id is not None
    assert order.billing_address_id is not None
    assert order.orderer_id is not None
    assert order.get_customer_name() == order.customer.name
