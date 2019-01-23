# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.utils.encoding import force_text
from django.utils.lru_cache import lru_cache
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField
from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import (
    get_permission_object_from_string, get_permissions_from_urls
)
from shuup.admin.utils.views import CreateOrUpdateView


def get_permissions_instances(permissions):
    permissions_instances = []
    for required_permission in permissions:
        permissions_instances.append(get_permission_object_from_string(required_permission))
    return permissions_instances


@lru_cache()
def get_perm_key(permission):
    name, module, __ = permission.natural_key()
    return name, module


class PermissionGroupForm(forms.ModelForm):
    class Meta:
        model = PermissionGroup
        exclude = ("permissions",)

    def __init__(self, *args, **kwargs):
        super(PermissionGroupForm, self).__init__(*args, **kwargs)
        self.fields["name"].help_text = _("The permission group name.")
        initial_members = self._get_initial_members()
        members_field = Select2MultipleField(
            model=get_user_model(),
            initial=[member.pk for member in initial_members],
            required=False,
            label=_("Members"),
            help_text=_("Set the users that belong to this permission group.")
        )
        members_field.widget.choices = [(member.pk, force_text(member)) for member in initial_members]
        self.fields["members"] = members_field

        initial_permissions = list(self.instance.permissions.values_list("pk", flat=True)) if self.instance.pk else []
        self.admin_modules = self._get_module_choices()

        for admin_module in self.admin_modules:
            admin_module.required_permissions_fields = []
            admin_module.per_view_permissions_fields = []

            for required_permission in get_permissions_instances(admin_module.get_required_permissions()):
                field_id = "perm:{}".format(required_permission.pk)
                self.fields[field_id] = forms.BooleanField(
                    required=False,
                    label=required_permission.name,
                    initial=(required_permission.pk in initial_permissions)
                )
                admin_module.required_permissions_fields.append(field_id)

            for permission in get_permissions_instances(get_permissions_from_urls(admin_module.get_urls())):
                field_id = "perm:{}".format(permission.pk)
                self.fields[field_id] = forms.BooleanField(
                    required=False,
                    label=permission.name,
                    initial=(permission.pk in initial_permissions)
                )
                admin_module.per_view_permissions_fields.append(field_id)

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
        permission_ids = set()

        for field, value in cleaned_data.items():
            if field.startswith("perm:") and value:
                permission_ids.add(field.split(":")[-1])

        cleaned_data["permissions"] = permission_ids
        return cleaned_data

    def save(self):
        obj = super(PermissionGroupForm, self).save()
        obj.permissions = set(self.cleaned_data["permissions"])
        obj.user_set = set(self.cleaned_data["members"])
        return obj


class PermissionGroupEditView(CreateOrUpdateView):
    model = PermissionGroup
    form_class = PermissionGroupForm
    template_name = "shuup/admin/permission_groups/edit.jinja"
    context_object_name = "permission_group"
    add_form_errors_as_messages = True
