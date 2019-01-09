# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.transaction import atomic
from django.http.response import HttpResponseRedirect
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from shuup.utils.excs import Problem


class RequestPasswordView(FormView):
    template_name = "shuup/admin/auth/request_password.jinja"

    def get_form_class(self):
        from shuup.admin.forms._auth import RequestPasswordForm
        return RequestPasswordForm

    def get_success_url(self):
        return "{}?email={}".format(reverse("shuup_admin:recover_password"), self.request.POST.get("email"))

    def get_form_kwargs(self):
        kwargs = super(RequestPasswordView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        form.save()
        msg = _("A reset password email was sent. Please, follow the instructions to set a new password.")
        messages.success(self.request, msg)
        return HttpResponseRedirect(reverse("shuup_admin:login"))


class ResetPasswordView(FormView):
    template_name = "shuup/admin/auth/reset_password.jinja"
    success_url = reverse_lazy("shuup_admin:login")
    token_generator = default_token_generator

    def get_form_class(self):
        from django.contrib.auth.forms import SetPasswordForm
        return SetPasswordForm

    def get_form_kwargs(self):
        kwargs = super(ResetPasswordView, self).get_form_kwargs()
        kwargs["user"] = self.get_target_user()
        return kwargs

    def get_target_user(self):
        uidb64 = self.kwargs["uidb64"]
        user_model = get_user_model()
        try:
            uid = urlsafe_base64_decode(uidb64)
            user = user_model._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, user_model.DoesNotExist):
            user = None
        return user

    def dispatch(self, request, *args, **kwargs):
        user = self.get_target_user()
        token = self.kwargs["token"]

        valid = (user is not None and self.token_generator.check_token(user, token))
        if not valid:
            raise Problem(_("This recovery link is invalid."))

        return super(ResetPasswordView, self).dispatch(request, *args, **kwargs)

    @atomic
    def form_valid(self, form):
        form.save()
        form.user.backend = "django.contrib.auth.backends.ModelBackend"
        login(self.request, form.user)
        messages.success(self.request, _("Password changed successfully!"))
        return HttpResponseRedirect(self.get_success_url())
