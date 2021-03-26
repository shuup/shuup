# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.views.dashboard import DashboardView
from shuup.admin.views.home import HomeView
from shuup.admin.views.wizard import WizardView
from shuup.apps.provides import override_provides
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse


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

    # no wizard spec defined so we should see a info block that everything is configured
    settings.SHUUP_SETUP_WIZARD_PANE_SPEC = []
    assert not has_block_with_text("wizard", rf, admin_user)


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


@pytest.mark.django_db
def test_product_blocks(rf, admin_user, settings):
    shop = get_default_shop()
    blocks = get_blocks(rf, admin_user)
    assert any(["New product" in action["text"] for b in blocks for action in b.actions])


@pytest.mark.django_db
def test_product_category_block(rf, admin_user):
    shop = get_default_shop()
    blocks = get_blocks(rf, admin_user)
    new_category_url = reverse("shuup_admin:category.new")
    assert any([new_category_url in action["url"] for b in blocks for action in b.actions])


@pytest.mark.django_db
def test_campaign_block(rf, admin_user):
    shop = get_default_shop()
    assert not has_block_with_text("campaign", rf, admin_user)


@pytest.mark.django_db
def test_users_block(rf, admin_user):
    shop = get_default_shop()
    assert has_block_with_text("users", rf, admin_user)


@pytest.mark.django_db
def test_cms_block(rf, admin_user):
    shop = get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = HomeView.as_view()(request)
    assert not any("web page" in b.text for b in response.context_data["blocks"])


@pytest.mark.django_db
def test_xtheme_block(rf, admin_user):
    shop = get_default_shop()
    blocks = get_blocks(rf, admin_user)
    assert not has_done_block_with_text("look and feel", rf, admin_user)
