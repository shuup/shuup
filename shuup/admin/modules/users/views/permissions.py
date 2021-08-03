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
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.forms.models import modelform_factory
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import UpdateView

from shuup.admin.forms.fields import ObjectSelect2MultipleField
from shuup.admin.toolbar import get_default_edit_toolbar
from shuup.admin.utils.urls import get_model_url
from shuup.utils.django_compat import force_text


class PermissionChangeFormBase(forms.ModelForm):
    old_password = forms.CharField(
        label=_("Your Password"),
        widget=forms.PasswordInput,
        help_text=_(
            "In order to allow making significant changes to accounts, we need "
            "to confirm that you know the password for the account you are using."
        ),
    )

    def __init__(self, changing_user, *args, **kwargs):
        super(PermissionChangeFormBase, self).__init__(*args, **kwargs)
        self.changing_user = changing_user
        if not getattr(self.changing_user, "is_superuser", False):
            self.fields.pop("is_superuser")

        if not (self.changing_user == self.instance or getattr(self.instance, "is_superuser", False)):
            # Only require old password when editing
            self.fields.pop("old_password")

        if "is_superuser" in self.fields:
            self.fields["is_superuser"].label = _("Superuser (Full rights) status")
            self.fields["is_superuser"].help_text = _(
                "Designates whether this user has all permissions without explicitly "
                "assigning them. Assigning Granular Permission Groups to a Superuser "
                "will not have any effect because Granular Permission Groups are only "
                " able to give more rights, but Superuser already has them all."
            )
        self.fields["is_staff"].label = _("Access to Admin Panel status")
        self.fields["is_staff"].help_text = _(
            "Designates whether this user can log into this admin site. Even "
            "Superusers should have this status enabled, otherwise they won't "
            "be able to access the Admin Panel."
        )

        permission_groups_field = ObjectSelect2MultipleField(
            model=PermissionGroup,
            required=False,
            label=_("Granular Permission Groups"),
            help_text=_(
                "Use Permission Groups to granularly give more permissions. User "
                "can belong to many groups and their permissions add and stack together. "
                "Search for `Permission Groups` to change these and add them to "
                "multiple users. Go to user account -> `Actions` -> `Edit Main "
                "Permissions` to add them to a specific user. Will not influence "
                "Superusers as they already have all the rights and can't be "
                "stripped of them without removing Superuser status first."
            ),
        )
        initial_groups = self._get_initial_groups()
        permission_groups_field.initial = [group.pk for group in initial_groups]
        permission_groups_field.widget.choices = [(group.pk, force_text(group)) for group in initial_groups]
        self.fields["permission_groups"] = permission_groups_field

    def _get_initial_groups(self):
        if self.instance.pk and hasattr(self.instance, "groups"):
            return self.instance.groups.all()
        else:
            return []

    def clean_old_password(self):
        """
        Validates that the `old_password` field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.changing_user.check_password(old_password):
            raise forms.ValidationError(
                _("Your old password was entered incorrectly. Please enter it again."),
                code="password_incorrect",
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
            if field not in self.cleaned_data:
                continue

            flag = self.cleaned_data[field]
            if self.changing_user == self.instance and not flag:
                self.add_error(
                    field,
                    _(
                        "You can't unset this status for yourself "
                        "due to security reasons. Use another account if you want to "
                        "remove permissions for this particular account."
                    ),
                )
        return self.cleaned_data

    def save(self):
        obj = super(PermissionChangeFormBase, self).save()
        obj.groups.clear()
        obj.groups.set(self.cleaned_data["permission_groups"])


class UserChangePermissionsView(UpdateView):
    template_name = "shuup/admin/users/change_permissions.jinja"
    model = settings.AUTH_USER_MODEL
    title = _("Change User Permissions")

    def get_form_class(self):
        return modelform_factory(
            model=get_user_model(), form=PermissionChangeFormBase, fields=("is_staff", "is_superuser")
        )

    def get_queryset(self):
        return get_user_model().objects.all()

    def get_toolbar(self):
        toolbar = get_default_edit_toolbar(
            self,
            "permissions_form",
            discard_url=get_model_url(self.object),
            with_split_save=False,
        )
        return toolbar

    def get_form_kwargs(self):
        kwargs = super(UserChangePermissionsView, self).get_form_kwargs()
        kwargs["changing_user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UserChangePermissionsView, self).get_context_data(**kwargs)
        context["toolbar"] = self.get_toolbar()
        context["title"] = _("Change Main Permissions: %s") % self.object
        return context

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Permissions changed for %s.") % self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return get_model_url(self.object)
