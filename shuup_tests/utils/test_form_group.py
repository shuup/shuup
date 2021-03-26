# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.forms.models import modelform_factory
from django.utils.encoding import force_text

from shuup.core.models import MutableAddress
from shuup.utils.form_group import FormGroup


class GeneralForm(forms.Form):
    field = forms.IntegerField(required=True)


def make_form_group(**kwargs):
    AddressForm = modelform_factory(MutableAddress, fields=("name",))
    fg = FormGroup(**kwargs)
    fg.add_form_def("address1", AddressForm, required=True)
    fg.add_form_def("address2", AddressForm, required=False)
    fg.add_form_def("general", GeneralForm, required=True)
    return fg


def test_form_group():
    fg = make_form_group()
    assert fg.forms["address1"].prefix == "address1"
    assert not fg.is_valid()
    assert not fg.full_clean()

    fg = make_form_group(data={})
    assert fg.is_bound
    assert not fg.is_valid()
    assert fg.errors.get("address1")

    fg = make_form_group(data={"address1-name": "herp", "general-field": "343"})
    assert fg.forms["address1"].is_bound
    assert fg.is_valid()
    assert not fg.errors


def test_form_group_initial():
    fg = make_form_group(initial={"address1-name": "Yes Sir"})
    assert "Yes Sir" in force_text(fg["address1"]["name"])
