# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.modules.contacts.forms import (
    CompanyContactBaseForm, PersonContactBaseForm
)
from shuup.core.models import PersonContact
from shuup.utils.excs import Problem
from shuup.utils.form_group import FormDef
from shuup.utils.importing import cached_load


class CompanyContactBaseFormPart(FormPart):
    priority = -1000

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            CompanyContactBaseForm,
            template_name="shuup/admin/contacts/_edit_base_form.jinja",
            required=True,
            kwargs={"instance": self.object if self.object.pk else None, "request": self.request}
        )

    def form_valid(self, form):
        self.object = form["base"].save()
        return self.object  # Identity may have changed (not the original object we put in)


class PersonContactBaseFormPart(FormPart):
    priority = -1000

    def get_user(self):
        bind_user_id = self.request.GET.get("user_id")
        if bind_user_id:
            bind_user = get_user_model().objects.get(pk=bind_user_id)
            if PersonContact.objects.filter(user=bind_user).exists():
                raise Problem(_("User `%(bind_user)s` already has a contact.", bind_user=bind_user))
        else:
            bind_user = None
        return bind_user

    def get_form_defs(self):
        yield TemplatedFormDef(
            "base",
            PersonContactBaseForm,
            template_name="shuup/admin/contacts/_edit_base_form.jinja",
            required=True,
            kwargs={
                "instance": self.object if self.object.pk else None,
                "user": self.get_user(),
                "request": self.request}
        )

    def form_valid(self, form):
        self.object = form["base"].save()
        return self.object  # Identity may have changed (not the original object we put in)


class ContactAddressesFormPart(FormPart):
    priority = -900

    def get_form_defs(self):
        initial = {}  # TODO: should we do this? model_to_dict(self.object, AddressForm._meta.fields)
        address_form_class = cached_load("SHUUP_ADDRESS_MODEL_FORM")
        yield FormDef(
            name="shipping_address", form_class=address_form_class,
            required=False, kwargs={"instance": self.object.default_shipping_address, "initial": initial}
        )
        yield FormDef(
            name="billing_address", form_class=address_form_class,
            required=False, kwargs={"instance": self.object.default_billing_address, "initial": initial}
        )
        # Using a pseudo formdef to group the two actual formdefs...
        yield TemplatedFormDef(
            name="addresses", form_class=forms.Form,
            required=False, template_name="shuup/admin/contacts/_edit_addresses_form.jinja"
        )

    def form_valid(self, form):
        for obj_key, form_name in [
            ("default_shipping_address", "shipping_address"),
            ("default_billing_address", "billing_address"),
        ]:
            addr_form = form[form_name]
            if addr_form.changed_data:
                addr = addr_form.save()
                setattr(self.object, obj_key, addr)
                self.object.save()
