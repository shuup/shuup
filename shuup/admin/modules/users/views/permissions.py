# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.forms.models import modelform_factory
from django.http.response import HttpResponseRedirect
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import UpdateView

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.shop_provider import get_shop
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.urls import get_model_url


class PermissionChangeFormBase(forms.ModelForm):
    old_password = forms.CharField(
        label=_("Your Password"),
        widget=forms.PasswordInput,
        help_text=_("For security purposes, we need your current password.")
    )

    def __init__(self, changing_user, *args, **kwargs):
        super(PermissionChangeFormBase, self).__init__(*args, **kwargs)
        self.changing_user = changing_user
        if getattr(self.instance, 'is_superuser', False) and not getattr(self.changing_user, 'is_superuser', False):
            self.fields.pop("is_superuser")

        if not (
            self.changing_user == self.instance or
            getattr(self.instance, 'is_superuser', False)
        ):
            # Only require old password when editing
            self.fields.pop("old_password")

        permission_groups_field = Select2MultipleField(
            model=PermissionGroup,
            required=False,
            label=_("Permission Groups"),
            help_text=_(
                "The permission groups that this user belongs to. "
                "Permission groups are configured through Contacts - Permission Groups."
            )
        )
        initial_groups = self._get_initial_groups()
        permission_groups_field.widget.choices = [(group.pk, force_text(group)) for group in initial_groups]
        self.fields["permission_groups"] = permission_groups_field

    def _get_initial_groups(self):
        if self.instance.pk and hasattr(self.instance, "groups"):
            return self.instance.groups.all()
        else:
            return []

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.changing_user.check_password(old_password):
            raise forms.ValidationError(
                _("Your old password was entered incorrectly. Please enter it again."),
                code='password_incorrect',
            )
        return old_password

    def clean_members(self):
        members = self.cleaned_data.get("members", [])
        return get_user_model().objects.filter(pk__in=members).all()

    def clean_permission_groups(self):
        permission_groups = self.cleaned_data.get("permission_groups", [])
        return PermissionGroup.objects.filter(pk__in=permission_groups)

    def clean(self):
        for field in ("is_staff", "is_superuser"):
            flag = self.cleaned_data[field]
            if self.changing_user == self.instance and not flag:
                self.add_error(field, _("You can't unset this status for yourself."))
        return self.cleaned_data

    def save(self):
        obj = super(PermissionChangeFormBase, self).save()
        obj.groups.clear()
        obj.groups = self.cleaned_data["permission_groups"]


class UserChangePermissionsView(UpdateView):
    template_name = "shuup/admin/users/change_permissions.jinja"
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

        if not getattr(self.object, "is_superuser", False):
            shop = get_shop(self.request)
            if getattr(self.object, "is_staff", False):
                shop.staff_members.add(self.object)
            else:
                shop.staff_members.remove(self.object)

        messages.success(self.request, _("Permissions changed for %s.") % self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return get_model_url(self.object)
