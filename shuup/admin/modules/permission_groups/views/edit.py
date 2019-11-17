# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import (
    get_permissions_from_group, get_permissions_from_urls,
    set_permissions_for_group
)
from shuup.admin.utils.views import CreateOrUpdateView
from shuup.utils.django_compat import force_text


class PermissionGroupForm(forms.ModelForm):
    class Meta:
        model = PermissionGroup
        exclude = ("permissions",)

    def __init__(self, *args, **kwargs):
        super(PermissionGroupForm, self).__init__(*args, **kwargs)
        self.fields["name"].help_text = _("The Permission Group name.")
        initial_members = self._get_initial_members()
        members_field = Select2MultipleField(
            model=get_user_model(),
            initial=[member.pk for member in initial_members],
            required=False,
            label=_("Members"),
            help_text=_("Set the users that belong to this Permission Group.")
        )
        members_field.widget.choices = [(member.pk, force_text(member)) for member in initial_members]
        self.fields["members"] = members_field

        initial_permissions = list(get_permissions_from_group(self.instance.pk)) if self.instance.pk else []
        self.admin_modules = self._get_module_choices()
        for admin_module in self.admin_modules:
            all_permissions_granted = True
            partial_permissions_granted = False
            admin_module.required_permissions_fields = []
            admin_module.per_view_permissions_fields = []

            for required_permission in admin_module.get_required_permissions():
                field_id = "perm:{}".format(required_permission)
                self.fields[field_id] = forms.BooleanField(
                    required=False,
                    label=required_permission,
                    initial=(required_permission in initial_permissions)
                )
                admin_module.required_permissions_fields.append(field_id)
                if required_permission in initial_permissions:
                    partial_permissions_granted = True
                else:
                    all_permissions_granted = False

            extra_permissions = (
                list(get_permissions_from_urls(admin_module.get_urls())) +
                list(admin_module.get_extra_permissions())
            )
            for permission in extra_permissions:
                field_id = "perm:{}".format(permission)
                self.fields[field_id] = forms.BooleanField(
                    required=False,
                    label=permission,
                    initial=(permission in initial_permissions)
                )
                admin_module.per_view_permissions_fields.append(field_id)
                if permission in initial_permissions:
                    partial_permissions_granted = True
                else:
                    all_permissions_granted = False

            admin_module.all_permissions_granted = all_permissions_granted
            admin_module.partial_permissions_granted = False if all_permissions_granted else partial_permissions_granted

    def _get_module_choices(self):
        modules = [module for module in get_modules() if module.name != "_Base_"]
        modules.sort(key=lambda module: module.name)
        return modules

    def _get_initial_members(self):
        if self.instance.pk:
            return self.instance.user_set.all()
        else:
            return []

    def clean_members(self):
        members = self.cleaned_data.get("members", [])
        return get_user_model().objects.filter(pk__in=members).all()

    def clean(self):
        cleaned_data = super(PermissionGroupForm, self).clean()
        permissions = set()

        for field, value in cleaned_data.items():
            if field.startswith("perm:") and value:
                permissions.add(field.split("perm:")[-1])

        cleaned_data["permissions"] = permissions
        return cleaned_data

    def save(self):
        obj = super(PermissionGroupForm, self).save()
        obj.user_set.set(set(self.cleaned_data["members"]))
        set_permissions_for_group(obj.pk, self.cleaned_data["permissions"])
        return obj


class PermissionGroupEditView(CreateOrUpdateView):
    model = PermissionGroup
    form_class = PermissionGroupForm
    template_name = "shuup/admin/permission_groups/edit.jinja"
    context_object_name = "permission_group"
    add_form_errors_as_messages = True
