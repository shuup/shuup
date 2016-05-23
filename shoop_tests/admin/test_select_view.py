# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import json
import pytest

from django.utils.translation import activate

from shoop.admin.views.select import MultiselectAjaxView
from shoop.core.models import CompanyContact, PersonContact
from shoop.testing.factories import create_product


@pytest.mark.django_db
def test_ajax_select_view_with_products(rf):
    activate("en")
    view = MultiselectAjaxView.as_view()
    results = _get_search_results(rf, view, "shoop.Product", "some str")
    assert len(results) == 0

    product_name_en = "The Product"
    product = create_product("the product", **{"name": product_name_en})

    product_name_fi = "product"
    product.set_current_language("fi")
    # Making sure we are not getting duplicates from translations
    product.name = "product"  # It seems that finnish translation overlaps with english name
    product.save()

    view = MultiselectAjaxView.as_view()
    results = _get_search_results(rf, view, "shoop.Product", "some str")
    assert len(results) == 0

    results = _get_search_results(rf, view, "shoop.Product", "product")
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_en

    activate("fi")
    results = _get_search_results(rf, view, "shoop.Product", "product")
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_fi


@pytest.mark.django_db
@pytest.mark.parametrize("contact_cls", [
    PersonContact, CompanyContact
])
def test_ajax_select_view_with_contacts(rf, contact_cls):
    view = MultiselectAjaxView.as_view()
    model_name = "shoop.%s" % contact_cls._meta.model_name
    results = _get_search_results(rf, view, model_name, "some str")
    assert len(results) == 0

    customer = contact_cls.objects.create(name="Michael Jackson", email="michael@example.com")
    results = _get_search_results(rf, view, model_name, "michael")
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_search_results(rf, view, model_name, "jacks")
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_search_results(rf, view, model_name, "el@ex")
    assert len(results) == 1
    assert results[0].get("id") == customer.id
    assert results[0].get("name") == customer.name

    results = _get_search_results(rf, view, model_name, "random")  # Shouldn't find anything with this
    assert len(results) == 0


def _get_search_results(rf, view, model_name, search_str):
    request = rf.get("sa/search", {
        "model": model_name,
        "search": search_str
    })
    response = view(request)
    assert response.status_code == 200
    return json.loads(response.content.decode("utf-8")).get("results")
