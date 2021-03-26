# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django import forms
from django.test import override_settings

from shuup import configuration
from shuup.apps.provides import override_provides
from shuup.core.models import AnonymousContact, get_person_contact
from shuup.core.utils.forms import MutableAddressForm
from shuup.front.checkout.addresses import AddressesPhase
from shuup.front.checkout.confirm import ConfirmForm
from shuup.front.views.checkout import BaseCheckoutView
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.front.utils import FieldTestProvider


def test_checkout_addresses_has_no_default_country():
    form = MutableAddressForm()
    assert form.fields["country"].initial is None


@override_settings(SHUUP_ADDRESS_HOME_COUNTRY="FI")
def test_checkout_addresses_has_default_country():
    form = MutableAddressForm()
    assert form.fields["country"].initial == "FI"


def test_required_address_fields():
    with override_settings(SHUUP_ADDRESS_FIELD_PROPERTIES={}):
        form = MutableAddressForm()
        assert form.fields["email"].required == False
        assert form.fields["email"].help_text != "Enter email"
        assert form.fields["phone"].help_text != "Enter phone"

    with override_settings(
        SHUUP_ADDRESS_FIELD_PROPERTIES={
            "email": {"required": True, "help_text": "Enter email"},
            "phone": {"help_text": "Enter phone"},
        }
    ):
        form = MutableAddressForm()
        assert form.fields["email"].required == True
        assert form.fields["email"].help_text == "Enter email"
        assert form.fields["phone"].help_text == "Enter phone"


class AddressesOnlyCheckoutView(BaseCheckoutView):
    phase_specs = ["shuup.front.checkout.addresses:AddressesPhase"]


@pytest.mark.django_db
def test_address_phase_authorized_user(rf, admin_user):
    request = apply_request_middleware(
        rf.get("/"), shop=get_default_shop(), customer=get_person_contact(admin_user), user=admin_user
    )
    view_func = AddressesPhase.as_view()
    resp = view_func(request)
    assert "company" not in resp.context_data["form"].form_defs


@pytest.mark.django_db
@pytest.mark.parametrize("allow_company_registration", [True, False])
def test_address_phase_anonymous_user(rf, allow_company_registration):
    shop = get_default_shop()
    configuration.set(shop, "allow_company_registration", allow_company_registration)
    request = apply_request_middleware(rf.get("/"), shop=shop)
    view_func = AddressesOnlyCheckoutView.as_view()
    resp = view_func(request, phase="addresses")
    assert bool("company" in resp.context_data["form"].form_defs) == allow_company_registration


@pytest.mark.django_db
def test_confirm_form_field_overrides(rf):
    with override_settings(SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES={}):
        request = apply_request_middleware(rf.get("/"), shop=get_default_shop())
        form = ConfirmForm(request=request)
        assert type(form.fields["comment"].widget) != forms.HiddenInput
        assert form.fields["marketing"].initial is False

    with override_settings(
        SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES={
            "comment": {"widget": forms.HiddenInput()},
            "marketing": {"initial": True},
        }
    ):
        form = ConfirmForm(request=request)
        assert type(form.fields["comment"].widget) == forms.HiddenInput
        assert form.fields["marketing"].initial is True


@pytest.mark.django_db
def test_confirm_form_field_provides(rf):
    with override_provides("checkout_confirm_form_field_provider", ["shuup_tests.front.utils.FieldTestProvider"]):
        request = apply_request_middleware(rf.post("/"), shop=get_default_shop())
        payload = {}  # make form invalid
        form = ConfirmForm(request=request, data=payload)
        assert FieldTestProvider.key in form.fields
        assert not form.is_valid()
        assert form.errors[FieldTestProvider.key][0] == FieldTestProvider.error_msg


@pytest.mark.django_db
def test_save_marketing_check(rf, admin_user):
    admin_contact = get_person_contact(admin_user)
    shop = get_default_shop()

    with override_settings(SHUUP_CHECKOUT_CONFIRM_FORM_PROPERTIES={}):
        request = apply_request_middleware(rf.get("/"), shop=shop, user=admin_user, customer=admin_contact)
        form = ConfirmForm(request=request)
        assert form.fields["marketing"].initial is False
        assert form.fields["marketing"].widget.__class__ == forms.CheckboxInput

        admin_contact.options = {}
        admin_contact.options["marketing_permission_asked"] = True
        admin_contact.save()

        form = ConfirmForm(request=request)
        assert form.fields["marketing"].initial is False
        assert form.fields["marketing"].widget.__class__ == forms.HiddenInput

        admin_contact.marketing_permission = True
        admin_contact.save()
        form = ConfirmForm(request=request)
        assert form.fields["marketing"].initial is True
        assert form.fields["marketing"].widget.__class__ == forms.HiddenInput

        # test with anonymous
        request = apply_request_middleware(rf.get("/"), shop=shop, user=admin_user, customer=AnonymousContact())
        form = ConfirmForm(request=request)
        assert form.fields["marketing"].initial is False
        assert form.fields["marketing"].widget.__class__ == forms.CheckboxInput
