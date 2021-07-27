# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.contrib.auth.models import Group as PermissionGroup
from django.utils.translation import ugettext_lazy as _

from shuup.admin.module_registry import get_modules
from shuup.admin.utils.permissions import (
    get_permissions_from_group,
    get_permissions_from_urls,
    set_permissions_for_group,
)
from shuup.admin.utils.views import CreateOrUpdateView


class PermissionGroupForm(forms.ModelForm):
    class Meta:
        model = PermissionGroup
        exclude = ("permissions",)

    def __init__(self, *args, **kwargs):
        super(PermissionGroupForm, self).__init__(*args, **kwargs)
        self.fields["name"].help_text = _("The Permission Group name.")

        initial_permissions = list(get_permissions_from_group(self.instance.pk)) if self.instance.pk else []
        self.admin_modules = self._get_module_choices()
        for admin_module in self.admin_modules:
            all_permissions_granted = True
            partial_permissions_granted = False
            admin_module.required_permissions_fields = []
            admin_module.per_view_permissions_fields = []
            help_texts = admin_module.get_permissions_help_texts()

            for required_permission in admin_module.get_required_permissions():
                field_id = "perm:{}".format(required_permission)
                self.fields[field_id] = forms.BooleanField(
                    required=False,
                    label=required_permission,
                    initial=(required_permission in initial_permissions),
                    help_text=help_texts.get(required_permission),
                )
                admin_module.required_permissions_fields.append(field_id)
                if required_permission in initial_permissions:
                    partial_permissions_granted = True
                else:
                    all_permissions_granted = False

            extra_permissions = list(get_permissions_from_urls(admin_module.get_urls())) + list(
                admin_module.get_extra_permissions()
            )
            for permission in extra_permissions:
                field_id = "perm:{}".format(permission)
                self.fields[field_id] = forms.BooleanField(
                    required=False,
                    label=permission,
                    initial=(permission in initial_permissions),
                    help_text=help_texts.get(permission),
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
        set_permissions_for_group(obj.pk, self.cleaned_data["permissions"])
        return obj


class PermissionGroupEditView(CreateOrUpdateView):
    model = PermissionGroup
    form_class = PermissionGroupForm
    template_name = "shuup/admin/permission_groups/edit.jinja"
    context_object_name = "permission_group"
    add_form_errors_as_messages = True
