# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth.models import Group as PermissionGroup
from django.utils.encoding import force_text

from shuup.admin.base import AdminModule
from shuup.admin.module_registry import get_modules, replace_modules
from shuup.admin.modules.permission_groups.views.edit import PermissionGroupEditView, PermissionGroupForm
from shuup.admin.utils.permissions import get_permissions_from_group
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.admin.fixtures.test_module import ARestrictedTestModule
from shuup_tests.utils.fixtures import regular_user


def get_default_permission_group():
    return PermissionGroup.objects.create(name="Test")


@pytest.mark.django_db
def test_permission_group_edit_view(rf, admin_user):
    get_default_shop()
    group = get_default_permission_group()
    view_func = PermissionGroupEditView.as_view()
    response = view_func(apply_request_middleware(rf.get("/"), pk=group.pk, user=admin_user))
    assert response.status_code == 200


@pytest.mark.django_db
def test_permission_group_form_updates_members():
    with replace_modules([ARestrictedTestModule]):
        modules = [m for m in get_modules()]
        test_module = modules[0]
        module_permissions = test_module.get_required_permissions()

        assert module_permissions

        group = get_default_permission_group()
        PermissionGroupForm(instance=group, prefix=None)

        assert not group.permissions.all()
        assert not group.user_set.all()

        data = {
            "name": "New Name",
        }
        for permission in ARestrictedTestModule().get_required_permissions():
            data["perm:%s" % permission] = permission

        form = PermissionGroupForm(instance=group, prefix=None, data=data)
        form.save()

        assert group.name == "New Name"
        assert set(module_permissions) == get_permissions_from_group(group)

        form = PermissionGroupForm(instance=group, prefix=None, data={"name": "Name"})
        form.save()

        assert not group.permissions.all()
        assert not group.user_set.all()


def test_only_show_modules_with_defined_names():
    """
    Make sure that only modules with defined names are show as choices
    in admin.
    """
    form = PermissionGroupForm(prefix=None)
    assert AdminModule.name not in form.admin_modules
