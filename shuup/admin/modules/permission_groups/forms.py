# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import defaultdict, OrderedDict

import six
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group as PermissionGroup
from django.contrib.auth.models import Permission
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shuup.admin.forms.fields import Select2MultipleField


class PermissionGroupForm(forms.ModelForm):
    class Meta:
        model = PermissionGroup
        exclude = ("permissions",)

    def __init__(self, *args, **kwargs):
        super(PermissionGroupForm, self).__init__(*args, **kwargs)
        self.initial_permissions = self._get_initial_permissions()

        self.fields["name"].help_text = _("The permission group name.")

        initial_members = self._get_initial_members()
        members_field = Select2MultipleField(
            model=get_user_model(),
            initial=[member.pk for member in initial_members],
            required=False,
            label=_("Members"),
            help_text=_(
                "Set the users that belong to this permission group."
            )
        )
        members_field.widget.choices = [(member.pk, force_text(member)) for member in initial_members]
        self.fields["members"] = members_field

        self.permission_code_to_name = {}
        self.model_permissions = defaultdict(list)
        for permission in Permission.objects.all():
            perm = "%s.%s" % (permission.content_type.app_label, permission.codename)
            self.permission_code_to_name[perm] = permission.name
            self.model_permissions[permission.content_type.model_class()._meta.verbose_name].append(perm)
            self.fields[perm] = self.get_permission_field(perm)

    def get_permission_field(self, permission):
        return forms.BooleanField(
            initial=bool(permission in self.initial_permissions),
            label=self.permission_code_to_name.get(permission, "Unnamed permission"),
            required=False
        )

    def get_model_permissions(self):
        return OrderedDict(sorted(self.model_permissions.items()))

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

    def clean_members(self):
        members = self.cleaned_data.get("members", [])
        return get_user_model().objects.filter(pk__in=members).all()

    def save(self):
        obj = super(PermissionGroupForm, self).save()
        permissions = set()
        for field_name, value in six.iteritems(self.cleaned_data):
            if field_name in ["members", "name"]:
                continue
            if value is None:
                continue
            app_label, code_name = field_name.split(".", 1)
            try:
                permission = Permission.objects.get(content_type__app_label=app_label, codename=code_name)
            except Permission.DoesNotExist:
                continue
            if value is True:
                permissions.add(permission.id)
        obj.permissions = permissions
        obj.user_set = set(self.cleaned_data["members"])
        return obj
