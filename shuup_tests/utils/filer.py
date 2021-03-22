# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.utils.permissions import set_permissions_for_group
from shuup.testing import factories
from shuup.utils.filer import can_see_root_folder


@pytest.mark.django_db
def test_can_see_root_folder(rf, admin_user):
    assert not can_see_root_folder(None)
    assert can_see_root_folder(admin_user)

    shop = factories.get_default_shop()
    staff_user = factories.UserFactory(is_staff=True)
    assert not can_see_root_folder(staff_user)
    permission_group = factories.get_default_permission_group()
    staff_user.groups.add(permission_group)
    shop.staff_members.add(staff_user)
    set_permissions_for_group(permission_group, ["media.view-all"])

    assert can_see_root_folder(staff_user)
