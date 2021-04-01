# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest

from shuup.admin.modules.manufacturers.views import ManufacturerListView
from shuup.admin.modules.sales_units.views import SalesUnitListView
from shuup.apps.provides import override_provides
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_view_custom_mass_actions(rf, admin_user):
    factories.get_default_shop()
    request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user)
    list_view_func = ManufacturerListView.as_view()

    # no mass actions
    response = list_view_func(request)
    data = json.loads(response.content.decode("utf-8"))
    assert not data["massActions"]

    # test with specific key
    with override_provides(
        "manufacturer_list_mass_actions_provider", ["shuup.testing.modules.mocker.mass_actions:DummyMassActionProvider"]
    ):
        response = list_view_func(request)
        data = json.loads(response.content.decode("utf-8"))
        identifiers = [action["key"] for action in data["massActions"]]
        assert "dummy_mass_action_1" in identifiers
        assert "dummy_mass_action_2" in identifiers

    list_view_func = SalesUnitListView.as_view()
    # test with global
    with override_provides(
        "admin_mass_actions_provider", ["shuup.testing.modules.mocker.mass_actions:DummyMassActionProvider"]
    ):
        response = list_view_func(request)
        data = json.loads(response.content.decode("utf-8"))
        identifiers = [action["key"] for action in data["massActions"]]
        assert "dummy_mass_action_1" in identifiers
        assert "dummy_mass_action_2" in identifiers
