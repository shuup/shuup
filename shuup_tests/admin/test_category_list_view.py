# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest

from shuup.core.models import CategoryStatus
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.importing import load


@pytest.mark.django_db
def test_list_view(rf, admin_user):
    shop = factories.get_default_shop()

    parent_category = factories.CategoryFactory(status=CategoryStatus.VISIBLE)
    parent_category.shops.add(shop)

    child_category = factories.CategoryFactory(status=CategoryStatus.VISIBLE)
    child_category.parent = parent_category
    child_category.save()
    child_category.shops.add(shop)

    view = load("shuup.admin.modules.categories.views:CategoryListView").as_view()
    request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user)
    response = view(request)
    assert 200 <= response.status_code < 300

    data = json.loads(response.content.decode("utf-8"))
    parent_data = _get_item_data(data, parent_category)
    assert _get_abstract_header(parent_data) == parent_category.name

    child_data = _get_item_data(data, child_category)
    assert _get_abstract_header(child_data) == child_category.name


def _get_item_data(data, item):
    return [item_data for item_data in data["items"] if item_data["_id"] == item.pk][0]


def _get_abstract_header(item_data):
    return [item for item in item_data["_abstract"] if item.get("class", "") == "header"][0]["text"]
