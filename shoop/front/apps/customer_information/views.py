# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shoop.core.models import get_person_contact, MutableAddress, PersonContact
from shoop.utils.form_group import FormGroup


class PersonContactForm(forms.ModelForm):
    class Meta:
        model = PersonContact
        fields = ("name", "phone", "email", "gender", "marketing_permission")

    def __init__(self, *args, **kwargs):
        super(PersonContactForm, self).__init__(*args, **kwargs)
        for field in ("name", "email"):
            self.fields[field].required = True


class AddressForm(forms.ModelForm):
    class Meta:
        model = MutableAddress
        fields = ("name", "phone", "email", "street", "street2", "postal_code", "city", "region", "country")

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        for field in ("email", "postal_code"):
            self.fields[field].required = True


class CustomerEditView(FormView):
    template_name = "shoop/customer_information/edit.jinja"

    def get_form(self, form_class):
        contact = get_person_contact(self.request.user)
        form_group = FormGroup(**self.get_form_kwargs())
        form_group.add_form_def("billing", AddressForm, kwargs={"instance": contact.default_billing_address})
        form_group.add_form_def("shipping", AddressForm, kwargs={"instance": contact.default_shipping_address})
        form_group.add_form_def("contact", PersonContactForm, kwargs={"instance": contact})
        return form_group

    def form_valid(self, form):
        contact = form["contact"].save()
        user = contact.user
        billing_address = form["billing"].save()
        shipping_address = form["shipping"].save()
        if billing_address.pk != contact.default_billing_address_id:  # Identity changed due to immutability
            contact.default_billing_address = billing_address
        if shipping_address.pk != contact.default_shipping_address_id:  # Identity changed due to immutability
            contact.default_shipping_address = shipping_address

        user.email = contact.email
        user.first_name = contact.first_name
        user.last_name = contact.last_name
        user.save()

        contact.save()
        messages.success(self.request, _("Account information saved successfully."))
        return redirect("shoop:customer_edit")
