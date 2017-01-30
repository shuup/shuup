# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.contrib.auth.models import Permission, Group as PermissionGroup
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType

from shuup.core.models import Order, Contact
from shuup.admin.base import AdminModule
from shuup.admin.module_registry import get_modules, replace_modules
from shuup.admin.modules.permission_groups.views.edit import (
    PermissionGroupEditView, PermissionGroupForm
)
from shuup.admin.utils.permissions import get_permission_object_from_string
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.admin.fixtures.test_module import ARestrictedTestModule
from shuup_tests.utils.fixtures import regular_user  # noqa


def get_default_permission_group():
    return PermissionGroup.objects.create(name="Test")


def migrate_permissions():
    order_content_type = ContentType.objects.get_for_model(Order)
    Permission.objects.create(
        codename="view_sales_dashboard",
        name="Can view sales dashboard",
        content_type=order_content_type,
    )

    contact_content_type = ContentType.objects.get_for_model(Contact)
    Permission.objects.create(
        codename="view_customers_dashboard",
        name="Can view customers dashboard",
        content_type=contact_content_type,
    )


@pytest.mark.django_db
def test_permission_group_edit_view(rf, admin_user):
    get_default_shop()
    migrate_permissions()
    group = get_default_permission_group()
    view_func = PermissionGroupEditView.as_view()
    response = view_func(apply_request_middleware(rf.get("/", user=admin_user), user=admin_user, pk=group.pk))
    assert response.status_code == 200


@pytest.mark.django_db
def test_permission_group_form_updates_members(regular_user):
    with replace_modules([ARestrictedTestModule]):
        modules = [m for m in get_modules()]
        test_module = modules[0]
        module_permissions = test_module.get_required_permissions()

        assert module_permissions

        group = get_default_permission_group()
        form = PermissionGroupForm(instance=group, prefix=None)

        assert not group.permissions.all()
        assert not group.user_set.all()

        data = {
            "name": "New Name",
            "modules": [force_text(test_module.name)],
            "members": [force_text(regular_user.pk)],
        }

        form = PermissionGroupForm(instance=group, prefix=None, data=data)
        form.save()

        module_permissions = [get_permission_object_from_string(m) for m in module_permissions]
        assert group.name == "New Name"
        # FIXME FIXME
        # assert set(module_permissions) == set(group.permissions.all())
        assert regular_user in group.user_set.all()

        form = PermissionGroupForm(instance=group, prefix=None, data={"name": "Name"})
        form.save()

        assert not group.permissions.all()
        assert not group.user_set.all()
