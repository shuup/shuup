# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.utils.forms import MutableAddressForm
from shuup.testing.factories import create_random_address, create_random_company, create_random_person
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_address_assigned_to_multiple_times_for_one_contact():
    person = create_random_person()
    address = create_random_address()
    person.default_billing_address = person.default_shipping_address = address
    person.save()

    assert person.default_billing_address_id == address.id
    assert person.default_shipping_address_id == address.id
    form = MutableAddressForm(instance=address)
    data = get_form_data(form, prepared=True)
    form = MutableAddressForm(data=data, instance=address)
    form.full_clean()
    assert not form.errors
    assert form.cleaned_data
    form.save()
    address.refresh_from_db()
    assert person.default_billing_address_id != address.id
    assert person.default_shipping_address_id != address.id


@pytest.mark.django_db
def test_address_assigned_for_multiple_contact():
    person1 = create_random_person()
    person2 = create_random_company()
    address = create_random_address()
    person1.default_billing_address = address
    person1.save()
    person2.default_shipping_address = address
    person2.save()

    assert person1.default_billing_address.id == address.id
    assert person2.default_shipping_address.id == address.id

    form = MutableAddressForm(instance=address)
    data = get_form_data(form, prepared=True)
    form = MutableAddressForm(data=data, instance=address)
    form.full_clean()
    assert not form.errors
    assert form.cleaned_data
    form.save()
    address.refresh_from_db()
    assert person1.default_billing_address_id != address.id
    assert person2.default_shipping_address_id != address.id
