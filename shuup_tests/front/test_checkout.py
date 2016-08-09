# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings

from shuup.core.models import get_person_contact
from shuup.front.checkout.addresses import AddressesPhase, AddressForm
from shuup.front.checkout.single_page import AddressForm as SinglePageAddressForm
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware


def test_checkout_addresses_has_no_default_country():
    form = AddressForm()
    assert form.fields["country"].initial is None


@override_settings(SHUUP_ADDRESS_HOME_COUNTRY="FI")
def test_checkout_addresses_has_default_country():
    form = AddressForm()
    assert form.fields["country"].initial == "FI"


def test_checkout_singlepage_addresses_has_no_default_country():
    form = SinglePageAddressForm()
    assert form.fields["country"].initial is None


@override_settings(SHUUP_ADDRESS_HOME_COUNTRY="FI")
def test_checkout_singlepage_addresses_has_default_country():
    form = SinglePageAddressForm()
    assert form.fields["country"].initial == "FI"


def test_required_address_fields():
    with override_settings(SHUUP_FRONT_ADDRESS_FIELD_PROPERTIES={}):
        form = SinglePageAddressForm()
        assert form.fields["email"].required == False
        assert form.fields["email"].help_text != "Enter email"
        assert form.fields["phone"].help_text != "Enter phone"

    with override_settings(
        SHUUP_FRONT_ADDRESS_FIELD_PROPERTIES={
            "email": {"required": True, "help_text": "Enter email"},
            "phone": {"help_text": "Enter phone"}
        }
    ):
        form = SinglePageAddressForm()
        assert form.fields["email"].required == True
        assert form.fields["email"].help_text == "Enter email"
        assert form.fields["phone"].help_text == "Enter phone"


@pytest.mark.django_db
def test_address_phase_authorized_user(rf, admin_user):
    request = apply_request_middleware(rf.get("/"), shop=get_default_shop(), customer=get_person_contact(admin_user))
    view_func = AddressesPhase.as_view()
    resp = view_func(request)
    assert 'company' not in resp.context_data['form'].form_defs


@pytest.mark.django_db
def test_address_phase_anonymous_user(rf):
    request = apply_request_middleware(rf.get("/"), shop=get_default_shop())
    view_func = AddressesPhase.as_view()
    resp = view_func(request)
    assert 'company' in resp.context_data['form'].form_defs
