# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.utils import translation

from shuup.front.apps.simple_search.views import (
    get_search_product_ids, SearchView
)
from shuup.testing.factories import (
    create_product, get_default_product, get_default_shop
)
from shuup.testing.utils import apply_request_middleware

UNLIKELY_STRING = "TJiCrQWaGChYNathovfViXPWO"
NO_RESULTS_FOUND_STRING = "No results found"

@pytest.mark.django_db
def test_simple_search_get_ids_works(rf):
    prod = get_default_product()
    bit = prod.name[:5]
    request = rf.get("/")
    assert prod.pk in get_search_product_ids(request, bit)
    assert prod.pk in get_search_product_ids(request, bit)  # Should use cache


@pytest.mark.django_db
def test_simple_search_view_works(rf):
    view = SearchView.as_view()
    prod = create_product(sku=UNLIKELY_STRING, shop=get_default_shop())
    query = prod.name[:8]

    # This test is pretty cruddy. TODO: Un-cruddify this test.
    resp = view(apply_request_middleware(rf.get("/")))
    assert query not in resp.rendered_content
    resp = view(apply_request_middleware(rf.get("/", {"q": query})))
    assert query in resp.rendered_content


@pytest.mark.django_db
def test_simple_search_word_finder(rf):
    view = SearchView.as_view()
    name = "Savage Garden"
    sku = UNLIKELY_STRING
    prod = create_product(
        sku=sku,
        name=name,
        keywords="truly, madly, deeply",
        description="Descriptive text",
        shop=get_default_shop()
    )

    resp = view(apply_request_middleware(rf.get("/")))
    assert prod not in resp.context_data["object_list"]

    partial_sku = sku[:int(len(sku)/2)]
    valid_searches = ["Savage", "savage", "truly", "madly", "truly madly", "truly garden", "text", sku, partial_sku]
    for query in valid_searches:
        resp = view(apply_request_middleware(rf.get("/", {"q": query})))
        assert name in resp.rendered_content

    invalid_searches = ["saavage", "", sku[::-1]]
    for query in invalid_searches:
        resp = view(apply_request_middleware(rf.get("/", {"q": query})))
        assert name not in resp.rendered_content


@pytest.mark.django_db
def test_normalize_spaces(rf):
    view = SearchView.as_view()
    prod = create_product(sku=UNLIKELY_STRING, name="Savage Garden", shop=get_default_shop())
    query = "\t Savage \t \t \n \r Garden \n"

    resp = view(apply_request_middleware(rf.get("/")))
    assert query not in resp.rendered_content
    resp = view(apply_request_middleware(rf.get("/", {"q": query})))
    assert query in resp.rendered_content


@pytest.mark.django_db
def test_simple_search_no_results(rf):
    with translation.override("xx"):  # use built-in translation
        get_default_shop()
        view = SearchView.as_view()
        resp = view(apply_request_middleware(rf.get("/", {"q": UNLIKELY_STRING})))
        assert NO_RESULTS_FOUND_STRING in resp.rendered_content
        resp = view(apply_request_middleware(rf.get("/")))
        assert NO_RESULTS_FOUND_STRING not in resp.rendered_content
