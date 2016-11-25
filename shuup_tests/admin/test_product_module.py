# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.module_registry import replace_modules
from shuup.admin.modules.products import ProductModule
from shuup.admin.modules.products.views.edit import ProductEditView
from shuup.admin.utils.urls import get_model_url
from shuup.admin.views.search import get_search_results
from shuup.core.models import ProductVisibility
from shuup.importer.admin_module import ImportAdminModule
from shuup.testing.factories import (
    create_product, get_default_product, get_default_shop
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.admin.utils import admin_only_urls
from shuup_tests.utils import empty_iterable


@pytest.mark.django_db
def test_product_module_search(rf, admin_user):
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    with replace_modules([ImportAdminModule, ProductModule]):
        with admin_only_urls():
            default_product = get_default_product()
            model_url = get_model_url(default_product)
            sku = default_product.sku
            assert any(sr.url == model_url for sr in get_search_results(request, query=sku))  # Queries work
            assert any(sr.is_action for sr in get_search_results(request, query=sku[:5]))  # Actions work
            assert empty_iterable(get_search_results(request, query=sku[:2]))  # Short queries don't


@pytest.mark.django_db
def test_product_edit_view_works_at_all(rf, admin_user):
    shop = get_default_shop()
    product = create_product("test-product", shop, default_price=200)
    shop_product = product.get_shop_instance(shop)
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_GROUPS
    shop_product.save()
    request = apply_request_middleware(rf.get("/"), user=admin_user)

    with replace_modules([ImportAdminModule, ProductModule]):
        with admin_only_urls():
            view_func = ProductEditView.as_view()
            response = view_func(request, pk=product.pk)
            response.render()
            assert (product.sku in response.rendered_content)  # it's probable the SKU is there
            response = view_func(request, pk=None)  # "new mode"
            assert response.rendered_content  # yeah, something gets rendered


@pytest.mark.django_db
def test_product_edit_view_with_params(rf, admin_user):
    get_default_shop()
    sku = "test-sku"
    name = "test name"
    request = apply_request_middleware(rf.get("/", {"name": name, "sku": sku}), user=admin_user)

    with replace_modules([ImportAdminModule, ProductModule]):
        with admin_only_urls():
            view_func = ProductEditView.as_view()
            response = view_func(request)
            assert (sku in response.rendered_content)  # it's probable the SKU is there
            assert (name in response.rendered_content)  # it's probable the name is there
