# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.apps.provides import get_provide_objects
from shuup.front.providers import FormDefinition, FormDefProvider, FormFieldDefinition, FormFieldProvider
from shuup.testing.factories import create_package_product


def get_unstocked_package_product_and_stocked_child(shop, supplier, child_logical_quantity=1):
    package_product = create_package_product("Package-Product-Test", shop=shop, supplier=supplier, children=1)

    quantity_map = package_product.get_package_child_to_quantity_map()
    assert len(quantity_map.keys()) == 1

    child_product = list(quantity_map.keys())[0]

    assert quantity_map[child_product] == 1

    supplier.adjust_stock(child_product.id, child_logical_quantity)

    stock_status = supplier.get_stock_status(child_product.id)
    assert stock_status.logical_count == child_logical_quantity

    return package_product, child_product


class FieldTestProvider(FormFieldProvider):
    # these are for test validation purposes only
    key = "accept_test_terms"
    label = "I have read and accept the test terms"
    error_msg = "Error! You must accept this in order to register or authenticate."

    def get_fields(self, **kwargs):
        field = forms.BooleanField(label=_(self.label), error_messages=dict(required=_(self.error_msg)))
        definition = FormFieldDefinition(name=self.key, field=field)
        return [definition]


class CompanyAgreementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.shop = kwargs.pop("shop")
        self.request = kwargs.pop("request")
        super(CompanyAgreementForm, self).__init__(*args, **kwargs)
        for provider_cls in get_provide_objects("front_registration_field_provider"):
            provider = provider_cls()
            for definition in provider.get_fields(request=self.request):
                self.fields[definition.name] = definition.field


class FormDefTestProvider(FormDefProvider):
    test_name = "agreement"
    test_form = CompanyAgreementForm

    def get_definitions(self, **kwargs):
        return [FormDefinition(self.test_name, self.test_form, required=True)]


def change_username_signal(sender, request, user, contact, *args, **kwargs):
    user.username = "changed_username"
    user.save()


def change_company_signal(sender, request, user, company, *args, **kwargs):
    user.username = "changed_username"
    user.save()
    company.name = "changed_name"
    company.save()


def login_allowed_signal(sender, request, user, *args, **kwargs):
    raise forms.ValidationError(
        "nope",
        code="login_allowed_signal",
    )


def checkout_complete_signal(sender, request, user, order, *args, **kwargs):
    order.ip_address = "127.0.0.2"
    order.save()
