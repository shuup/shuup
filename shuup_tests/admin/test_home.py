# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from django.core.urlresolvers import reverse

from shuup.admin.views.dashboard import DashboardView
from shuup.admin.views.home import HomeView
from shuup.admin.views.wizard import WizardView
from shuup.apps.provides import override_provides
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware


def get_blocks(rf, admin_user):
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = HomeView.as_view()(request)
    assert response.status_code == 200
    return response.context_data.get("blocks", [])


def has_block_with_text(text, rf, admin_user):
    return any(text in b.text for b in get_blocks(rf, admin_user))


def has_done_block_with_text(text, rf, admin_user):
    return any(text in b.text for b in get_blocks(rf, admin_user) if b.done)


@pytest.mark.django_db
def test_home_wizard_block(rf, admin_user, settings):
    # wizard completion block should be present
    get_default_shop()
    assert has_block_with_text("wizard", rf, admin_user)

    # no wizard spec defined so we shouldn't see the wizard block
    settings.SHUUP_SETUP_WIZARD_PANE_SPEC = []
    assert has_done_block_with_text("wizard", rf, admin_user)


@pytest.mark.django_db
def test_wizard_redirect(rf, admin_user, settings):
    settings.SHUUP_SETUP_WIZARD_PANE_SPEC = []
    shop = get_default_shop()
    shop.maintenance_mode = True
    shop.save()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = WizardView.as_view()(request)
    assert response.status_code == 302
    assert response["Location"] == reverse("shuup_admin:home")


@pytest.mark.django_db
def test_dashboard_redirect(rf, admin_user, settings):
    settings.SHUUP_SETUP_WIZARD_PANE_SPEC = []
    shop = get_default_shop()
    shop.maintenance_mode = True
    shop.save()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = DashboardView.as_view()(request)
    assert response.status_code == 302
    assert response["Location"] == reverse("shuup_admin:home")

    shop.maintenance_mode = False
    shop.save()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = DashboardView.as_view()(request)
    assert response.status_code == 200
