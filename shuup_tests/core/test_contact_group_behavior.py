# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.core.models import GroupAvailabilityBehaviorComponent, OrderLineType, PersonContact
from shuup.testing.factories import (
    create_product,
    create_random_person,
    get_default_customer_group,
    get_default_payment_method,
    get_default_supplier,
)

from .test_order_creator import seed_source


@pytest.mark.django_db
def test_contact_group_behavior(admin_user):
    payment_method = get_default_payment_method()
    group = get_default_customer_group()
    _assign_component_for_service(payment_method, [group])

    person = create_random_person()
    person.user = admin_user
    person.save()
    source = _get_source_for_contact(admin_user, payment_method)
    assert source.customer == person
    assert group not in person.groups.all()
    _test_service_availability(source, payment_method, False)

    person.groups.add(group)
    assert group in person.groups.all()
    _test_service_availability(source, payment_method, True)


@pytest.mark.django_db
def test_without_groups(admin_user):
    payment_method = get_default_payment_method()
    _assign_component_for_service(payment_method, [])

    person = create_random_person()
    person.user = admin_user
    person.save()
    source = _get_source_for_contact(admin_user, payment_method)
    assert source.customer == person
    _test_service_availability(source, payment_method, False)


@pytest.mark.django_db
def test_with_multiple_groups(admin_user):
    payment_method = get_default_payment_method()
    group = get_default_customer_group()
    person = create_random_person()
    groups = [group, person.get_default_group()]
    _assign_component_for_service(payment_method, groups)

    person.user = admin_user
    person.save()
    source = _get_source_for_contact(admin_user, payment_method)
    assert source.customer == person
    assert len([group for group in person.groups.all() if group in groups]) == 1
    _test_service_availability(source, payment_method, True)


@pytest.mark.django_db
def test_unsaved_contact(admin_user):
    payment_method = get_default_payment_method()
    _assign_component_for_service(payment_method, [PersonContact.get_default_group()])
    person = PersonContact(name="Kalle")
    source = _get_source_for_contact(admin_user, payment_method)
    source.customer = person
    assert not person.pk and not source.customer.pk
    _test_service_availability(source, payment_method, False)


def _assign_component_for_service(service, groups):
    assert service.behavior_components.count() == 0
    component = GroupAvailabilityBehaviorComponent.objects.create()
    for group in groups:
        component.groups.add(group)
    service.behavior_components.add(component)


def _get_source_for_contact(user, payment_method):
    source = seed_source(user)
    supplier = get_default_supplier()
    product = create_product(sku="random", shop=source.shop, supplier=supplier, default_price=3.33)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=supplier,
        quantity=1,
        base_unit_price=source.create_price(1),
    )
    source.payment_method = payment_method
    return source


def _test_service_availability(source, service, is_available):
    assert service.behavior_components.count() == 1
    unavailability_reasons = list(service.get_unavailability_reasons(source))
    assert bool(unavailability_reasons) != is_available
