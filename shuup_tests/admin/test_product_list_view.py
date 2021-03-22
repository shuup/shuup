# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from django.test import override_settings

from shuup.core.settings import SHUUP_ENABLE_MULTIPLE_SUPPLIERS
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
    request = apply_request_middleware(rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user)
    response = view(request)
    assert 200 <= response.status_code < 300

    data = json.loads(response.content.decode("utf-8"))
    product_data = [item for item in data["items"] if item["_id"] == shop_product.pk][0]
    assert product_data["primary_category"] == factories.get_default_category().name
    assert product_data["categories"] == factories.get_default_category().name
    assert product_data["categories"] == factories.get_default_category().name

    # Suppliers not available by default since multiple suppliers is not enabled
    assert "suppliers" not in product_data


@pytest.mark.django_db
def test_list_view_with_multiple_suppliers(rf, admin_user):
    shop = factories.get_default_shop()

    product = factories.create_product(sku="test", shop=shop)
    shop_product = product.get_shop_instance(shop)
    shop_product.primary_category = factories.get_default_category()
    shop_product.save()
    shop_product.categories.add(shop_product.primary_category)

    # Also one product with supplier
    supplier = factories.get_default_supplier()
    product2 = factories.create_product(sku="test2", shop=shop, supplier=supplier)
    shop_product2 = product2.get_shop_instance(shop)
    shop_product2.primary_category = factories.get_default_category()
    shop_product2.save()
    shop_product2.categories.add(shop_product.primary_category)

    with override_settings(SHUUP_ENABLE_MULTIPLE_SUPPLIERS=True):
        view = load("shuup.admin.modules.products.views:ProductListView").as_view()
        request = apply_request_middleware(
            rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user
        )
        response = view(request)
        assert 200 <= response.status_code < 300

        data = json.loads(response.content.decode("utf-8"))
        assert len(data["items"]) == 2
        product_data = [item for item in data["items"] if item["_id"] == shop_product.pk][0]
        assert product_data["primary_category"] == factories.get_default_category().name
        assert product_data["categories"] == factories.get_default_category().name
        assert product_data["categories"] == factories.get_default_category().name
        assert product_data["suppliers"] == ""

        product_data2 = [item for item in data["items"] if item["_id"] == shop_product2.pk][0]
        assert product_data2["suppliers"] == factories.get_default_supplier().name

    with override_settings(SHUUP_ADMIN_SUPPLIER_PROVIDER_SPEC="shuup.testing.supplier_provider.FirstSupplierProvider"):
        view = load("shuup.admin.modules.products.views:ProductListView").as_view()
        request = apply_request_middleware(
            rf.get("/", {"jq": json.dumps({"perPage": 100, "page": 1})}), user=admin_user
        )
        response = view(request)
        assert 200 <= response.status_code < 300

        data = json.loads(response.content.decode("utf-8"))
        assert len(data["items"]) == 1
