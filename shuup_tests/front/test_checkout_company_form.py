# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup import configuration
from shuup.core.models import get_person_contact
from shuup.front.checkout.addresses import CompanyForm
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


def test_required_fields(rf, admin_user):
    request = apply_request_middleware(
        rf.get("/"), shop=factories.get_default_shop(), customer=get_person_contact(admin_user), user=admin_user
    )

    form = CompanyForm(request=request)
    assert form.fields["name"].required == False
    assert form.fields["tax_number"].required == False


def test_clean(rf, admin_user):
    shop = factories.get_default_shop()
    request = apply_request_middleware(rf.get("/"), shop=shop, customer=get_person_contact(admin_user), user=admin_user)
    form = CompanyForm(data={"name": "Test Oy"}, request=request)
    form.full_clean()
    assert not form.is_valid()
    assert "Tax number is required with the company name." in form.errors["tax_number"][0]

    form = CompanyForm(data={"tax_number": "123"}, request=request)
    form.full_clean()
    assert not form.is_valid()
    assert "Company name is required with the tax number." in form.errors["name"][0]

    # Enable tax number validation
    configuration.set(shop, "validate_tax_number", True)

    # Test with invalid non vat
    form = CompanyForm(data={"name": "Test Oy", "tax_number": "123"}, request=request)
    form.full_clean()
    assert not form.is_valid()
    assert len(form.errors["tax_number"]) == 2  # One for missing tax number and one for failing validation

    # Test with invalid vat-like tax number
    form = CompanyForm(data={"name": "Test Oy", "tax_number": "FI123456789"}, request=request)
    form.full_clean()
    assert not form.is_valid()
    assert len(form.errors["tax_number"]) == 2  # One for missing tax number and one for failing validation

    form = CompanyForm(data={"name": "Test Oy", "tax_number": "FI12345678"}, request=request)
    form.full_clean()
    assert form.is_valid()
