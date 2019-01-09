# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import messages
from django.utils.encoding import force_text
from django.views.generic import FormView

from shuup.testing.factories import (
    create_random_company, create_random_contact_group, create_random_order,
    create_random_person, create_random_product_attribute
)


class Mockers(object):
    """
    Namespace object for mocker methods.

    The docstrings for the callables are user-visible.
    """

    def mock_order(self, **kwargs):
        """ Create a random order """
        shop = kwargs.pop("shop")
        return create_random_order(completion_probability=0.8, shop=shop)

    def mock_person(self, **kwargs):
        """ Create a random person """
        shop = kwargs.pop("shop")
        return create_random_person(shop=shop)

    def mock_company(self, **kwargs):
        """ Create a random company """
        shop = kwargs.pop("shop")
        return create_random_company(shop=shop)

    def mock_customer_group(self, **kwargs):
        """ Create a random contact group """
        return create_random_contact_group()

    def mock_product_attribute(self, **kwargs):
        """ Create a random product attribute """
        return create_random_product_attribute()


class MockerForm(forms.Form):
    type = forms.ChoiceField(widget=forms.RadioSelect())
    count = forms.IntegerField(min_value=1, max_value=100, initial=1)


class MockerView(FormView):
    form_class = MockerForm
    template_name = "shuup_testing/mocker.jinja"
    mockers = Mockers()

    def get_mockers(self):
        return [
            (
                name,
                force_text(getattr(getattr(self.mockers, name, None), "__doc__") or name).strip()
            ) for name in dir(self.mockers) if name.startswith("mock_")
        ]

    def get_form(self, form_class=None):
        form = super(MockerView, self).get_form(form_class)
        form.fields["type"].choices = self.get_mockers()
        return form

    def form_valid(self, form):
        data = form.cleaned_data
        mocker = getattr(self.mockers, data["type"], None)
        assert callable(mocker)
        for n in range(data["count"]):
            try:
                value = mocker(shop=self.request.shop)
                if value:
                    messages.success(self.request, "Created: %s" % value)
            except Exception as e:
                if settings.DEBUG:
                    raise
                messages.error(self.request, "Error: %s" % e)
        return self.get(self.request)
