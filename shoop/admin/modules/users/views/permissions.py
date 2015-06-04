# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django import forms
from django.forms.models import modelform_factory
from django.http.response import HttpResponseRedirect
from django.views.generic.edit import UpdateView
from shoop.admin.toolbar import get_default_edit_toolbar
from shoop.admin.utils.urls import get_model_url
from django.utils.translation import ugettext_lazy as _


class PermissionChangeFormBase(forms.ModelForm):
    old_password = forms.CharField(
        label=_("Your Password"),
        widget=forms.PasswordInput,
        help_text=_("For security purposes, we need your current password.")
    )

    def __init__(self, changing_user, *args, **kwargs):
        super(PermissionChangeFormBase, self).__init__(*args, **kwargs)
        self.changing_user = changing_user
        if self.instance.is_superuser and not self.changing_user.is_superuser:
            self.fields.pop("is_superuser")

        if not (
            self.changing_user == self.instance or
            self.instance.is_superuser
        ):
            # Only require old password when editing
            self.fields.pop("old_password")

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.changing_user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

    def clean(self):
        for field in ("is_staff", "is_superuser"):
            flag = self.cleaned_data[field]
            if self.changing_user == self.instance and not flag:
                self.add_error(field, _("You can't unset this status for yourself."))
        return self.cleaned_data


class UserChangePermissionsView(UpdateView):
    template_name = "shoop/admin/users/change_permissions.jinja"
    model = settings.AUTH_USER_MODEL
    title = _("Change User Permissions")

    def get_form_class(self):
        return modelform_factory(
            model=get_user_model(),
            form=PermissionChangeFormBase,
            fields=("is_staff", "is_superuser")
        )

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_toolbar(self):
        toolbar = get_default_edit_toolbar(
            self,
            "permissions_form",
            discard_url=get_model_url(self.object),
            with_split_save=False
        )
        return toolbar

    def get_form_kwargs(self):
        kwargs = super(UserChangePermissionsView, self).get_form_kwargs()
        kwargs["changing_user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UserChangePermissionsView, self).get_context_data(**kwargs)
        context["toolbar"] = self.get_toolbar()
        context["title"] = _("Change Permissions: %s") % self.object
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Permissions changed for %s.") % self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return get_model_url(self.object)
