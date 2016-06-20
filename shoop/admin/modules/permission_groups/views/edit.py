# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.forms.fields import Select2MultipleField
from shoop.admin.module_registry import get_modules
from shoop.admin.utils.permissions import get_permission_object_from_string
from shoop.admin.utils.views import CreateOrUpdateView


class PermissionGroupForm(forms.ModelForm):
    class Meta:
        model = PermissionGroup
        exclude = ("permissions",)

    def __init__(self, *args, **kwargs):
        super(PermissionGroupForm, self).__init__(*args, **kwargs)
        initial_permissions = self._get_initial_permissions()
        self.fields["modules"] = forms.MultipleChoiceField(
            choices=sorted(self._get_module_choices()),
            initial=self._get_enabled_modules(initial_permissions),
            required=False,
            label=_("Module Permissions"),
            help_text=_("Modules with the same permissions as selected modules will be added automatically.")
        )
        initial_members = self._get_initial_members()
        members_field = Select2MultipleField(
            model=get_user_model(),
            initial=[member.pk for member in initial_members],
            required=False,
            label=_("Members"),
        )
        members_field.widget.choices = [(member.pk, force_text(member)) for member in initial_members]
        self.fields["members"] = members_field

    def _get_module_choices(self):
        return set((force_text(module.name), force_text(module.name)) for module in get_modules())

    def _get_initial_members(self):
        if self.instance.pk:
            return self.instance.user_set.all()
        else:
            return []

    def _get_initial_permissions(self):
        permissions = set()
        if self.instance.pk:
            for perm in self.instance.permissions.all():
                name, module, _ = perm.natural_key()
                permissions.add("%s.%s" % (module, name))
        return permissions

    def _get_enabled_modules(self, permissions):
        if not self.instance.pk:
            return []
        permissions = set(permissions)
        modules = []
        for module in get_modules():
            # Ignore modules that haven't configured a name
            if module.name != "_Base_" and set(module.get_required_permissions()).issubset(permissions):
                modules.append(force_text(module.name))
        return modules

    def _get_required_permissions(self, modules):
        permissions = set()
        for module in [m for m in get_modules() if m.name in modules]:
            permissions.update(set(module.get_required_permissions()))
        return permissions

    def clean_members(self):
        members = self.cleaned_data.get("members", [])

        return get_user_model().objects.filter(pk__in=members).all()

    def clean(self):
        cleaned_data = super(PermissionGroupForm, self).clean()

        permissions = set()
        modules = cleaned_data.pop("modules", [])
        required_permissions = self._get_required_permissions(modules)

        for permission in required_permissions:
            permissions.add(get_permission_object_from_string(permission))

        cleaned_data["required_permissions"] = permissions

        return cleaned_data

    def save(self):
        obj = super(PermissionGroupForm, self).save()
        obj.permissions = set(self.cleaned_data["required_permissions"])
        obj.user_set = set(self.cleaned_data["members"])
        return obj


class PermissionGroupEditView(CreateOrUpdateView):
    model = PermissionGroup
    form_class = PermissionGroupForm
    template_name = "shoop/admin/permission_groups/edit.jinja"
    context_object_name = "permission_group"
    add_form_errors_as_messages = True
