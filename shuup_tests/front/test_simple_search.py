# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.utils import translation

from shuup.core import cache
from shuup.core.models import ProductVisibility, ShopProductVisibility
from shuup.front.apps.simple_search.forms import get_search_product_ids
from shuup.front.apps.simple_search.views import SearchView
from shuup.testing.factories import (
    create_product,
    create_random_person,
    get_default_product,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware

UNLIKELY_STRING = "TJiCrQWaGChYNathovfViXPWO"
NO_RESULTS_FOUND_STRING = "No results found"


@pytest.mark.django_db
def test_simple_search_get_ids_works(rf):
    cache.clear()
    prod = get_default_product()
    bit = prod.name[:5]
    request = apply_request_middleware(rf.get("/"))
    assert prod.pk in get_search_product_ids(request, bit)
    assert prod.pk in get_search_product_ids(request, bit)  # Should use cache


@pytest.mark.django_db
def test_simple_search_view_works(rf):
    cache.clear()
    view = SearchView.as_view()
    prod = create_product(sku=UNLIKELY_STRING, shop=get_default_shop())
    query = prod.name[:8]

    # This test is pretty cruddy. TODO: Un-cruddify this test.
    resp = view(apply_request_middleware(rf.get("/")))
    assert query not in resp.rendered_content
    resp = view(apply_request_middleware(rf.get("/", {"q": query})))
    assert query in resp.rendered_content


@pytest.mark.django_db
def test_simple_search_word_finder(rf, reindex_catalog):
    cache.clear()
    view = SearchView.as_view()
    name = "Savage Garden"
    sku = UNLIKELY_STRING
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    prod = create_product(
        sku=sku,
        name=name,
        keywords="truly, madly, deeply",
        description="Descriptive text",
        shop=shop,
        supplier=supplier,
    )
    reindex_catalog()
    resp = view(apply_request_middleware(rf.get("/")))
    assert prod not in resp.context_data["object_list"], "No query no results"

    partial_sku = sku[: int(len(sku) / 2)]
    valid_searches = ["Savage", "savage", "truly", "madly", "truly madly", "truly garden", "text", sku, partial_sku]
    for query in valid_searches:
        resp = view(apply_request_middleware(rf.get("/", {"q": query})))
        assert name in resp.rendered_content

    invalid_searches = ["saavage", "", sku[::-1]]
    for query in invalid_searches:
        resp = view(apply_request_middleware(rf.get("/", {"q": query})))
        assert name not in resp.rendered_content


@pytest.mark.parametrize(
    "visibility,show_in_search",
    [
        (ShopProductVisibility.NOT_VISIBLE, False),
        (ShopProductVisibility.LISTED, False),
        (ShopProductVisibility.SEARCHABLE, True),
        (ShopProductVisibility.ALWAYS_VISIBLE, True),
    ],
)
@pytest.mark.django_db
def test_product_searchability(rf, visibility, show_in_search, reindex_catalog):
    cache.clear()
    view = SearchView.as_view()
    name = "Savage Garden"
    sku = UNLIKELY_STRING

    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    product = create_product(sku, name=name, shop=shop, supplier=supplier)
    shop_product = product.get_shop_instance(shop)
    shop_product.visibility = visibility
    shop_product.save()
    reindex_catalog()

    resp = view(apply_request_middleware(rf.get("/", {"q": "savage"})))
    assert (name in resp.rendered_content) == show_in_search


@pytest.mark.django_db
def test_normalize_spaces(rf, reindex_catalog):
    cache.clear()
    view = SearchView.as_view()
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    create_product(sku=UNLIKELY_STRING, name="Savage Garden", shop=shop, supplier=supplier)
    reindex_catalog()
    query = "\t Savage \t \t \n \r Garden \n"

    resp = view(apply_request_middleware(rf.get("/")))
    assert query not in resp.rendered_content
    resp = view(apply_request_middleware(rf.get("/", {"q": query})))
    assert query in resp.rendered_content


@pytest.mark.django_db
def test_simple_search_no_results(rf):
    cache.clear()
    with translation.override("xx"):  # use built-in translation
        get_default_shop()
        view = SearchView.as_view()
        resp = view(apply_request_middleware(rf.get("/", {"q": UNLIKELY_STRING})))
        assert NO_RESULTS_FOUND_STRING in resp.rendered_content
        resp = view(apply_request_middleware(rf.get("/")))
        assert NO_RESULTS_FOUND_STRING in resp.rendered_content, "No query string no results"


@pytest.mark.django_db
def test_simple_search_with_non_public_products(rf, reindex_catalog):
    cache.clear()
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    customer = create_random_person()
    name = "Some Test Name For Product"
    product = create_product("sku", name=name, shop=shop, supplier=supplier, default_price=10)
    shop_product = product.get_shop_instance(shop)
    shop_product.visibility = ShopProductVisibility.SEARCHABLE
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_LOGGED_IN
    shop_product.save()
    reindex_catalog()

    view = SearchView.as_view()
    request = apply_request_middleware(rf.get("/", {"q": "Test name"}), customer=customer)
    resp = view(request)
    assert name in resp.rendered_content
