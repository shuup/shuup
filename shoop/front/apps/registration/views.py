# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
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

from shoop.front.template_helpers import urls


def activation_complete(request):
    messages.success(request, _("Activation successful!"))
    if urls.has_url('shoop:customer_edit'):
        return redirect('shoop:customer_edit')
    else:
        return redirect(settings.LOGIN_REDIRECT_URL)


def registration_complete(request):
    messages.success(request, _("Registration complete. Please follow the instructions sent to your email address."))
    return redirect(settings.LOGIN_REDIRECT_URL)


class RegistrationViewMixin(object):
    template_name = "shoop/registration/register.jinja"

    def get_success_url(self, request, user):
        url = self.request.REQUEST.get(REDIRECT_FIELD_NAME)
        if url and is_safe_url(url, request.get_host()):
            return url
        return ('shoop:registration_complete', (), {})


class RegistrationNoActivationView(RegistrationViewMixin, simple_views.RegistrationView):
    pass


class RegistrationWithActivationView(RegistrationViewMixin, default_views.RegistrationView):
    pass


class RegistrationView(View):
    def dispatch(self, request, *args, **kwargs):
        if settings.SHOOP_REGISTRATION_REQUIRES_ACTIVATION:
            view_class = RegistrationWithActivationView
        else:
            view_class = RegistrationNoActivationView

        return view_class.as_view()(request, *args, **kwargs)


class ActivationView(default_views.ActivationView):
    template_name = "shoop/registration/activation_failed.jinja"

    def get_success_url(self, request, user):
        return ('shoop:registration_activation_complete', (), {})
