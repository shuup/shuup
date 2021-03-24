# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from registration.backends.default import views as default_views
from registration.backends.simple import views as simple_views

from shuup.core.models import get_company_contact, get_person_contact
from shuup.front.apps.registration.forms import CompanyRegistrationForm
from shuup.front.template_helpers import urls
from shuup.front.utils.companies import allow_company_registration


def activation_complete(request):
    messages.success(request, _("Activation successful"))
    if urls.has_url("shuup:customer_edit"):
        return redirect("shuup:customer_edit")
    else:
        return redirect(settings.LOGIN_REDIRECT_URL)


def registration_complete(request):
    if settings.SHUUP_REGISTRATION_REQUIRES_ACTIVATION:
        messages.success(
            request, _("Registration complete. Please follow the instructions sent to your email address.")
        )
    return redirect(settings.LOGIN_REDIRECT_URL)


class RegistrationViewMixin(object):
    template_name = "shuup/registration/register.jinja"

    def get_success_url(self, *args, **kwargs):
        url = self.request.GET.get(REDIRECT_FIELD_NAME) or self.request.POST.get(REDIRECT_FIELD_NAME)
        if url and is_safe_url(url, self.request.get_host()):
            return url
        return ("shuup:registration_complete", (), {})

    def get_form_kwargs(self):
        kwargs = super(RegistrationViewMixin, self).get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["auto_id"] = "id_registration_for_%s"
        return kwargs

    def register(self, form):
        user = super(RegistrationViewMixin, self).register(form)
        get_person_contact(user).add_to_shop(self.request.shop)
        return user


class RegistrationNoActivationView(RegistrationViewMixin, simple_views.RegistrationView):
    pass


class RegistrationWithActivationView(RegistrationViewMixin, default_views.RegistrationView):
    SEND_ACTIVATION_EMAIL = False


class RegistrationView(View):
    def dispatch(self, request, *args, **kwargs):
        if settings.SHUUP_REGISTRATION_REQUIRES_ACTIVATION:
            view_class = RegistrationWithActivationView
        else:
            view_class = RegistrationNoActivationView

        return view_class.as_view()(request, *args, **kwargs)


class CompanyRegistrationView(RegistrationViewMixin, default_views.RegistrationView):
    template_name = "shuup/registration/company_register.jinja"
    form_class = CompanyRegistrationForm

    SEND_ACTIVATION_EMAIL = False

    def dispatch(self, request, *args, **kwargs):
        if not allow_company_registration(request.shop):
            return redirect("shuup:registration_register")
        return super(CompanyRegistrationView, self).dispatch(request, *args, **kwargs)

    def register(self, form):
        user = super(CompanyRegistrationView, self).register(form)

        if settings.SHUUP_ENABLE_MULTIPLE_SHOPS and settings.SHUUP_MANAGE_CONTACTS_PER_SHOP:
            company = get_company_contact(user)
            company.add_to_shop(self.request.shop)


class ActivationView(default_views.ActivationView):
    template_name = "shuup/registration/activation_failed.jinja"

    def get_success_url(self, *args, **kwargs):
        return ("shuup:registration_activation_complete", (), {})
