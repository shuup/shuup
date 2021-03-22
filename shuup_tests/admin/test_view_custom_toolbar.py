# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.modules.contact_group_price_display.views import (
    ContactGroupPriceDisplayEditView,
    ContactGroupPriceDisplayListView,
)
from shuup.apps.provides import override_provides
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_custom_view_toolbar_buttons(rf, admin_user):
    factories.get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    list_view_func = ContactGroupPriceDisplayListView.as_view()
    edit_view_func = ContactGroupPriceDisplayEditView.as_view()

    with override_provides(
        "contact_group_price_list_toolbar_provider",
        ["shuup.testing.modules.mocker.toolbar:ContactGroupPriceDisplayButtonProvider"],
    ):
        list_response = list_view_func(request)
        list_response.render()
        list_content = list_response.content.decode("utf-8")
        assert "btn-contact-group-hello" in list_content

        edit_response = edit_view_func(request)
        edit_response.render()
        edit_response = edit_response.content.decode("utf-8")
        assert "btn-contact-group-hello" not in edit_response

    # use global provider - all views should have that button
    with override_provides(
        "admin_toolbar_button_provider", ["shuup.testing.modules.mocker.toolbar:ContactGroupPriceDisplayButtonProvider"]
    ):
        list_response = list_view_func(request)
        list_response.render()
        list_content = list_response.content.decode("utf-8")
        assert "btn-contact-group-hello" in list_content

        edit_response = edit_view_func(request)
        edit_response.render()
        edit_response = edit_response.content.decode("utf-8")
        assert "btn-contact-group-hello" in edit_response
