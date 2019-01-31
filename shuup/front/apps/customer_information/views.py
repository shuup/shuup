# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import password_change
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, TemplateView
from registration.signals import user_registered

from shuup.core.models import (
    CompanyContact, get_company_contact, get_person_contact, MutableAddress,
    SavedAddress
)
from shuup.front.utils.companies import (
    allow_company_registration, company_registration_requires_approval
)
from shuup.front.views.dashboard import DashboardViewMixin
from shuup.utils.form_group import FormGroup
from shuup.utils.importing import cached_load

from .forms import CompanyContactForm, PersonContactForm, SavedAddressForm
from .notify_events import CompanyAccountCreated


class PasswordChangeView(DashboardViewMixin, TemplateView):
    template_name = "shuup/customer_information/change_password.jinja"

    def post(self, *args, **kwargs):
        response = password_change(
            self.request,
            post_change_redirect="shuup:customer_edit",
            template_name=self.template_name
        )
        if response.status_code == 302:
            messages.success(self.request, _("Password successfully changed."))
        return response

    def get_context_data(self, **kwargs):
        context = super(PasswordChangeView, self).get_context_data(**kwargs)
        context["form"] = PasswordChangeForm(user=self.request.user)
        return context


class CustomerEditView(DashboardViewMixin, FormView):
    template_name = "shuup/customer_information/edit_customer.jinja"

    def get_form(self, form_class=None):
        contact = get_person_contact(self.request.user)
        form_group = FormGroup(**self.get_form_kwargs())
        address_form_class = cached_load("SHUUP_ADDRESS_MODEL_FORM")
        form_group.add_form_def("billing", address_form_class, kwargs={"instance": contact.default_billing_address})
        form_group.add_form_def("shipping", address_form_class, kwargs={"instance": contact.default_shipping_address})
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

        if not bool(get_company_contact(self.request.user)):  # Only update user details for non-company members
            user.email = contact.email
            user.first_name = contact.first_name
            user.last_name = contact.last_name
            user.save()

        contact.save()
        messages.success(self.request, _("Account information saved successfully."))
        return redirect("shuup:customer_edit")


class CompanyEditView(DashboardViewMixin, FormView):
    template_name = "shuup/customer_information/edit_company.jinja"

    def dispatch(self, request, *args, **kwargs):
        if not (bool(get_company_contact(self.request.user)) or allow_company_registration(self.request.shop)):
            return redirect("shuup:customer_edit")
        return super(CompanyEditView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        user = self.request.user
        company = get_company_contact(user)
        person = get_person_contact(user)
        form_group = FormGroup(**self.get_form_kwargs())
        address_form_class = cached_load("SHUUP_ADDRESS_MODEL_FORM")
        form_group.add_form_def(
            "billing",
            address_form_class,
            kwargs={
                "instance": _get_default_address_for_contact(company, "default_billing_address", person)
            }
        )
        form_group.add_form_def(
            "shipping",
            address_form_class,
            kwargs={
                "instance": _get_default_address_for_contact(company, "default_shipping_address", person)
            }
        )
        form_group.add_form_def("contact", CompanyContactForm, kwargs={"instance": company})
        return form_group

    def form_valid(self, form):
        company = form["contact"].save(commit=False)
        is_new = not bool(company.pk)
        company.save()
        user = self.request.user
        # TODO: Should this check if contact will be created? Or should we expect create always?
        person = get_person_contact(user)
        person.add_to_shop(self.request.shop)
        company.members.add(person)
        company.add_to_shop(self.request.shop)
        billing_address = form["billing"].save()
        shipping_address = form["shipping"].save()
        if billing_address.pk != company.default_billing_address_id:  # Identity changed due to immutability
            company.default_billing_address = billing_address
        if shipping_address.pk != company.default_shipping_address_id:  # Identity changed due to immutability
            company.default_shipping_address = shipping_address

        message = _("Company information saved successfully.")
        # If company registration requires activation,
        # company will be created as inactive.
        if is_new and company_registration_requires_approval(self.request.shop):
            company.is_active = False
            message = _("Company information saved successfully. "
                        "Please follow the instructions sent to your email address.")

        company.save()
        if is_new:
            user_registered.send(sender=self.__class__,
                                 user=self.request.user,
                                 request=self.request)
            CompanyAccountCreated(contact=company, customer_email=company.email).run(shop=self.request.shop)

        messages.success(self.request, message)
        return redirect("shuup:company_edit")

    def get_context_data(self, **kwargs):
        context = super(CompanyEditView, self).get_context_data(**kwargs)
        context["pending_company_approval"] = CompanyContact.objects.filter(
            members__in=[self.request.customer], is_active=False).exists()
        return context


class AddressBookView(DashboardViewMixin, TemplateView):
    template_name = "shuup/customer_information/addressbook/index.jinja"

    def get_context_data(self, **kwargs):
        context = super(AddressBookView, self).get_context_data(**kwargs)
        context["addresses"] = SavedAddress.objects.filter(owner=self.request.customer)
        context["customer"] = self.request.customer
        return context


class AddressBookEditView(DashboardViewMixin, FormView):
    template_name = "shuup/customer_information/addressbook/edit.jinja"
    form_class = SavedAddressForm
    instance = None

    def dispatch(self, request, *args, **kwargs):
        try:
            self.instance = SavedAddress.objects.get(pk=kwargs.get("pk", 0), owner=self.request.customer)
        except:
            self.instance = None
        return super(AddressBookEditView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form_group = FormGroup(**self.get_form_kwargs())
        address_kwargs = {}
        saved_address_kwargs = {}
        if self.instance:
            address_kwargs["instance"] = self.instance.address
            saved_address_kwargs["initial"] = {
                "role": self.instance.role,
                "status": self.instance.status,
                "title": self.instance.title,
            }

        form_group.add_form_def("address", cached_load("SHUUP_ADDRESS_MODEL_FORM"), kwargs=address_kwargs)
        form_group.add_form_def(
            "saved_address",
            SavedAddressForm,
            kwargs=saved_address_kwargs
        )
        return form_group

    def form_valid(self, form):
        address_form = form["address"]
        if self.instance:
            # expect old
            address = MutableAddress.objects.get(pk=self.instance.address.pk)
            for k, v in six.iteritems(address_form.cleaned_data):
                setattr(address, k, v)
            address.save()
        else:
            address = address_form.save()
        owner = self.request.customer
        saf = form["saved_address"]
        saved_address, updated = SavedAddress.objects.update_or_create(
            owner=owner,
            address=address,
            defaults={
                "title": saf.cleaned_data.get("title"),
                "role": saf.cleaned_data.get("role"),
                "status": saf.cleaned_data.get("status")
            }
        )
        messages.success(self.request, _("Address information saved successfully."))
        return redirect("shuup:address_book_edit", pk=saved_address.pk)


def delete_address(request, pk):
    try:
        SavedAddress.objects.get(pk=pk, owner=request.customer).delete()
    except SavedAddress.DoesNotExist:
        messages.error(request, _("Cannot remove address"))
    return redirect("shuup:address_book")


def _get_default_address_for_contact(contact, address_attr, fallback_contact):
    if contact and getattr(contact, address_attr, None):
        return getattr(contact, address_attr)
    if fallback_contact and getattr(fallback_contact, address_attr, None):
        return getattr(fallback_contact, address_attr)
    return None
