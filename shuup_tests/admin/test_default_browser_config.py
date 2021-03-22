# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.modules.media import MediaModule
from shuup.admin.template_helpers.shuup_admin import get_browser_urls
from shuup.admin.utils.permissions import get_permissions_from_urls, set_permissions_for_group
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse


@pytest.mark.django_db
def test_browser_config_as_superuser(rf, admin_user):
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    urls = get_browser_urls(request)
    assert urls["media"] == reverse("shuup_admin:media.browse")


@pytest.mark.django_db
def test_browser_config_as_shop_staff(rf):
    shop = factories.get_default_shop()
    staff_user = factories.UserFactory(is_staff=True)
    permission_group = factories.get_default_permission_group()
    staff_user.groups.add(permission_group)
    shop.staff_members.add(staff_user)

    request = apply_request_middleware(rf.post("/"), user=staff_user)
    urls = get_browser_urls(request)
    # staff does not have media permission
    assert urls["media"] is None

    set_permissions_for_group(permission_group, ["media.browse"])
    urls = get_browser_urls(request)
    assert urls["media"] == reverse("shuup_admin:media.browse")

    media_module_permission_urls = set(get_permissions_from_urls(MediaModule().get_urls()))
    assert "media.browse" in media_module_permission_urls
    assert "shuup_admin:media.browse" not in media_module_permission_urls
