# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings
from django.test import override_settings
from django.utils.translation import activate

from shuup.admin.modules.categories.views import CategoryEditView
from shuup.admin.modules.shops.views import ShopEditView
from shuup.apps.provides import override_provides
from shuup.core import cache
from shuup.front.utils.sorts_and_filters import get_configuration
from shuup.testing.factories import get_default_category, get_default_shop
from shuup.testing.utils import apply_request_middleware

DEFAULT_FORM_MODIFIERS = [
    "shuup.front.forms.product_list_modifiers.SortProductListByName",
    "shuup.front.forms.product_list_modifiers.SortProductListByPrice",
    "shuup.front.forms.product_list_modifiers.ManufacturerProductListFilter",
]


@pytest.mark.django_db
def test_sorts_and_filter_in_shop_edit(rf, admin_user):
    cache.clear()
    activate("en")
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        with override_provides("front_extend_product_list_form", DEFAULT_FORM_MODIFIERS):
            shop = get_default_shop()
            view = ShopEditView.as_view()
            assert get_configuration(shop=shop) == settings.SHUUP_FRONT_DEFAULT_SORT_CONFIGURATION
            data = {
                "base-name__en": shop.name,
                "base-public_name__en": shop.public_name,
                "base-status": shop.status.value,
                "base-currency": shop.currency,
                "base-prices_include_tax": shop.prices_include_tax,
                "base-languages": "en",
                "order_configuration-order_min_total": 0,
                "order_configuration-order_reference_number_length": 18,
                "product_list_facets-sort_products_by_name": True,
                "product_list_facets-sort_products_by_name_ordering": 11,
                "product_list_facets-sort_products_by_price": False,
                "product_list_facets-sort_products_by_price_ordering": 32,
                "product_list_facets-filter_products_by_manufacturer": False,
                "product_list_facets-filter_products_by_manufacturer_ordering": 1,
            }
            request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
            response = view(request, pk=shop.pk)
            if hasattr(response, "render"):
                response.render()
            assert response.status_code in [200, 302]

            expected_configurations = {
                "sort_products_by_name": True,
                "sort_products_by_name_ordering": 11,
                "sort_products_by_price": False,
                "sort_products_by_price_ordering": 32,
                "filter_products_by_manufacturer": False,
                "filter_products_by_manufacturer_ordering": 1,
            }
            assert get_configuration(shop=shop) == expected_configurations


@pytest.mark.django_db
def test_sorts_and_filter_in_category_edit(rf, admin_user):
    get_default_shop()
    cache.clear()
    activate("en")
    with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        with override_provides("front_extend_product_list_form", DEFAULT_FORM_MODIFIERS):
            category = get_default_category()
            view = CategoryEditView.as_view()
            assert get_configuration(category=category) == settings.SHUUP_FRONT_DEFAULT_SORT_CONFIGURATION
            data = {
                "base-name__en": category.name,
                "base-status": category.status.value,
                "base-visibility": category.visibility.value,
                "base-ordering": category.ordering,
                "product_list_facets-sort_products_by_name": True,
                "product_list_facets-sort_products_by_name_ordering": 6,
                "product_list_facets-sort_products_by_price": False,
                "product_list_facets-sort_products_by_price_ordering": 32,
                "product_list_facets-filter_products_by_manufacturer": True,
                "product_list_facets-filter_products_by_manufacturer_ordering": 1,
            }
            request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
            response = view(request, pk=category.pk)
            if hasattr(response, "render"):
                response.render()
            assert response.status_code in [200, 302]
            # not overriding
            assert get_configuration(category=category) == settings.SHUUP_FRONT_DEFAULT_SORT_CONFIGURATION

            data["product_list_facets-override_default_configuration"] = True
            request = apply_request_middleware(rf.post("/", data=data), user=admin_user)
            response = view(request, pk=category.pk)
            if hasattr(response, "render"):
                response.render()
            assert response.status_code in [200, 302]
            expected_configurations = {
                "override_default_configuration": True,
                "sort_products_by_name": True,
                "sort_products_by_name_ordering": 6,
                "sort_products_by_price": False,
                "sort_products_by_price_ordering": 32,
                "filter_products_by_manufacturer": True,
                "filter_products_by_manufacturer_ordering": 1,
            }
            assert get_configuration(category=category) == expected_configurations
