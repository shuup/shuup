# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import pytest

from shuup.testing import factories

from shuup.testing.utils import apply_request_middleware
from shuup.utils.importing import load


@pytest.mark.django_db
def test_list_view(rf, admin_user):
    shop = factories.get_default_shop()
    product = factories.create_product(sku="test", shop=shop)
    shop_product = product.get_shop_instance(shop)
    shop_product.primary_category = factories.get_default_category()
    shop_product.save()
    shop_product.categories.add(shop_product.primary_category)

    view = load("shuup.admin.modules.products.views:ProductListView").as_view()
    request = apply_request_middleware(rf.get("/", {
        "jq": json.dumps({"perPage": 100, "page": 1})
    }), user=admin_user)
    response = view(request)
    assert 200 <= response.status_code < 300

    data = json.loads(response.content.decode("utf-8"))
    product_data = [item for item in data["items"] if item["_id"] == shop_product.pk][0]
    assert product_data["primary_category"] == factories.get_default_category().name
    assert product_data["categories"] == factories.get_default_category().name
