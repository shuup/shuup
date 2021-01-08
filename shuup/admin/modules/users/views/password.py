# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, UpdateView

from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.front.apps.auth.views import RecoverPasswordForm
from shuup.utils.excs import Problem


class PasswordChangeForm(forms.Form):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
        'password_incorrect': _("Your old password was entered incorrectly. Please enter it again."),
    }
    old_password = forms.CharField(
        label=_("Your Password"),
        widget=forms.PasswordInput,
        help_text=_("For security purposes, we need your current password.")
    )
    password1 = forms.CharField(label=_("New Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("New Password (again)"), widget=forms.PasswordInput)

    def __init__(self, changing_user, target_user, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.changing_user = changing_user
        self.target_user = target_user
        if getattr(self.target_user, 'is_superuser', False) and not getattr(self.changing_user, 'is_superuser', False):
            raise Problem(_("You can not change the password of a superuser."))

        if not (
            self.changing_user == self.target_user or
            getattr(self.target_user, 'is_superuser', False)
        ):
            # Only require old password when changing your own or a superuser's password.
            self.fields.pop("old_password")

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def clean_old_password(self):
        """
        Validates that the `old_password` field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.changing_user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

    def save(self, commit=True):
        self.target_user.set_password(self.cleaned_data["password1"])
        if commit:
            self.target_user.save()
        return self.target_user


class UserChangePasswordView(UpdateView):
    form_class = PasswordChangeForm
    template_name = "shuup/admin/users/change_password.jinja"
    model = settings.AUTH_USER_MODEL
    title = _("Change User Password")

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_toolbar(self):
        toolbar = get_default_edit_toolbar(
            self,
            "change_password_form",
            discard_url=get_model_url(self.object),
            with_split_save=False
        )
        return toolbar

    def get_form_kwargs(self):
        kwargs = super(UserChangePasswordView, self).get_form_kwargs()
        kwargs["target_user"] = kwargs.pop("instance")
        kwargs["changing_user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UserChangePasswordView, self).get_context_data(**kwargs)
        context["toolbar"] = self.get_toolbar()
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Password changed for %s.") % self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return get_model_url(self.object)


class UserResetPasswordView(DetailView):
    model = settings.AUTH_USER_MODEL
    template_name = "shuup/admin/users/reset_password.jinja"
    title = _("Reset User Password")

    def get_queryset(self):
        return get_user_model().objects.all()

    def process_user(self, user):
        if "shuup.front.apps.auth" not in settings.INSTALLED_APPS:
            raise Problem(_(u"Error! The `shuup.front.apps.auth` app needs to be enabled for password reset."))

        r = RecoverPasswordForm()
        r.request = self.request
        if r.process_user(user, self.request):
            messages.success(self.request, _(u"Password recovery email sent to %(email)s.") %
                             {"email": getattr(user, 'email', '')})
        else:
            raise Problem(_(u"Error! Sending the password recovery email failed."))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.process_user(self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return get_model_url(self.object)
