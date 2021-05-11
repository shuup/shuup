# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import REDIRECT_FIELD_NAME
from django.db.transaction import atomic
from django.http import HttpResponseRedirect
from django.utils.http import is_safe_url, urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, TemplateView

from shuup.core.utils.forms import RecoverPasswordForm
from shuup.utils.django_compat import is_authenticated, reverse_lazy
from shuup.utils.excs import Problem
from shuup.utils.importing import cached_load


class LoginView(FormView):
    template_name = "shuup/user/login.jinja"
    form_class = cached_load("SHUUP_AUTH_LOGIN_FORM_SPEC")

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context[REDIRECT_FIELD_NAME] = self.request.GET.get(REDIRECT_FIELD_NAME)
        return context

    def get_form_kwargs(self):
        kwargs = super(LoginView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_form(self, form_class=None, id_prefix="auth"):
        if form_class is None:
            form_class = self.get_form_class()

        kwargs = self.get_form_kwargs()
        kwargs["auto_id"] = "id_{}_for_%s".format(id_prefix)

        form = form_class(**kwargs)
        form.fields[REDIRECT_FIELD_NAME] = forms.CharField(
            widget=forms.HiddenInput, required=False, initial=self.request.GET.get(REDIRECT_FIELD_NAME)
        )
        return form

    def form_valid(self, form):
        user = form.get_user()
        if user is not None:
            login(self.request, user)
        return super(LoginView, self).form_valid(form)

    def get_success_url(self):
        url = self.request.POST.get(REDIRECT_FIELD_NAME)
        if url and is_safe_url(url, self.request.get_host()):
            return url
        return settings.LOGIN_REDIRECT_URL


class LogoutView(TemplateView):
    template_name = "shuup/user/logout.jinja"

    def dispatch(self, request, *args, **kwargs):
        if is_authenticated(request.user):
            logout(request)
        return super(LogoutView, self).dispatch(request, *args, **kwargs)


class RecoverPasswordView(FormView):
    template_name = "shuup/user/recover_password.jinja"
    form_class = RecoverPasswordForm
    success_url = reverse_lazy("shuup:recover_password_sent")

    def form_valid(self, form):
        """
        :type form: RecoverPasswordForm
        """
        form.save(request=self.request)
        return HttpResponseRedirect(self.get_success_url())


class RecoverPasswordConfirmView(FormView):
    template_name = "shuup/user/recover_password_confirm.jinja"
    form_class = SetPasswordForm
    token_generator = default_token_generator
    success_url = reverse_lazy("shuup:recover_password_complete")

    def get_form_kwargs(self):
        kwargs = super(RecoverPasswordConfirmView, self).get_form_kwargs()
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

        valid = user is not None and self.token_generator.check_token(user, token)
        if not valid:
            raise Problem(_("Error! This recovery link is invalid."))

        return super(RecoverPasswordConfirmView, self).dispatch(request, *args, **kwargs)

    @atomic
    def form_valid(self, form):
        """
        :type form: SetPasswordForm
        """
        form.save()
        form.user.backend = "django.contrib.auth.backends.ModelBackend"
        login(self.request, form.user)
        return HttpResponseRedirect(self.get_success_url())


class RecoverPasswordSentView(TemplateView):
    template_name = "shuup/user/recover_password_sent.jinja"


class RecoverPasswordCompleteView(TemplateView):
    template_name = "shuup/user/recover_password_complete.jinja"
