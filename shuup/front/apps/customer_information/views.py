# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, TemplateView

from shuup.core.models import CompanyContact, get_company_contact, SavedAddress
from shuup.front.utils.companies import allow_company_registration
from shuup.front.views.dashboard import DashboardViewMixin
from shuup.utils.django_compat import reverse_lazy
from shuup.utils.importing import cached_load


class CustomPasswordChangeView(PasswordChangeView):
    template_name = "shuup/customer_information/change_password.jinja"
    success_url = reverse_lazy("shuup:customer_edit")
    form_class = PasswordChangeForm

    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs)
        if response.status_code == 302:
            messages.success(self.request, _("Password changed."))
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CustomerEditView(DashboardViewMixin, FormView):
    template_name = "shuup/customer_information/edit_customer.jinja"

    def get_form_class(self):
        return cached_load("SHUUP_CUSTOMER_INFORMATION_EDIT_FORM")

    def get_form_kwargs(self):
        kwargs = super(CustomerEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Account information was saved."))
        return redirect("shuup:customer_edit")


class CompanyEditView(DashboardViewMixin, FormView):
    template_name = "shuup/customer_information/edit_company.jinja"

    def dispatch(self, request, *args, **kwargs):
        if not (bool(get_company_contact(self.request.user)) or allow_company_registration(self.request.shop)):
            return redirect("shuup:customer_edit")
        return super(CompanyEditView, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return cached_load("SHUUP_COMPANY_INFORMATION_EDIT_FORM")

    def get_form_kwargs(self):
        kwargs = super(CompanyEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        form.save()
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
    instance = None

    def dispatch(self, request, *args, **kwargs):
        try:
            self.instance = SavedAddress.objects.get(pk=kwargs.get("pk", 0), owner=self.request.customer)
        except Exception:
            self.instance = None
        return super(AddressBookEditView, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return cached_load("SHUUP_ADDRESS_BOOK_EDIT_FORM")

    def get_form_kwargs(self):
        kwargs = super(AddressBookEditView, self).get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["instance"] = self.instance
        return kwargs

    def form_valid(self, form):
        saved_address = form.save()
        messages.success(self.request, _("Address information was saved."))
        return redirect("shuup:address_book_edit", pk=saved_address.pk)


def delete_address(request, pk):
    try:
        SavedAddress.objects.get(pk=pk, owner=request.customer).delete()
    except SavedAddress.DoesNotExist:
        messages.error(request, _("Cannot remove address because it doesn't exist."))
    return redirect("shuup:address_book")
