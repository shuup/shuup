# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import json
import pytest

from django.contrib.auth import get_user_model
from django.utils.translation import activate

from shuup.admin.views.select import MultiselectAjaxView
from shuup.core.models import CompanyContact, get_person_contact, PersonContact
from shuup.testing.factories import create_product, get_default_category
from shuup_tests.utils.fixtures import regular_user


def _get_search_results(rf, view, model_name, search_str):
    request = rf.get("sa/search", {
        "model": model_name,
        "search": search_str
    })
    response = view(request)
    assert response.status_code == 200
    return json.loads(response.content.decode("utf-8")).get("results")


@pytest.mark.django_db
def test_ajax_select_view_with_products(rf):
    activate("en")
    view = MultiselectAjaxView.as_view()
    results = _get_search_results(rf, view, "shuup.Product", "some str")
    assert len(results) == 0

    product_name_en = "The Product"
    product = create_product("the product", **{"name": product_name_en})

    product_name_fi = "product"
    product.set_current_language("fi")
    # Making sure we are not getting duplicates from translations
    product.name = "product"  # It seems that finnish translation overlaps with english name
    product.save()

    view = MultiselectAjaxView.as_view()
    results = _get_search_results(rf, view, "shuup.Product", "some str")
    assert len(results) == 0

    results = _get_search_results(rf, view, "shuup.Product", "product")
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_en

    activate("fi")
    results = _get_search_results(rf, view, "shuup.Product", "product")
    assert len(results) == 1
    assert results[0].get("id") == product.id
    assert results[0].get("name") == product_name_fi

    product.soft_delete()
    results = _get_search_results(rf, view, "shuup.Product", "product")
    assert len(results) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("contact_cls", [
    PersonContact, CompanyContact
])
def test_ajax_select_view_with_contacts(rf, contact_cls):
    view = MultiselectAjaxView.as_view()
    model_name = "shuup.%s" % contact_cls._meta.model_name
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


@pytest.mark.django_db
def test_ajax_select_view_with_categories(rf):
    activate("en")
    view = MultiselectAjaxView.as_view()
    results = _get_search_results(rf, view, "shuup.Category", "some str")
    assert len(results) == 0

    category = get_default_category()
    results = _get_search_results(rf, view, "shuup.Category", category.name)
    assert len(results) == 1

    category.soft_delete()
    results = _get_search_results(rf, view, "shuup.Category", category.name)
    assert len(results) == 0


@pytest.mark.django_db
def test_multiselect_inactive_users_and_contacts(rf, regular_user):
    """
    Make sure inactive users and contacts are filtered from search results.
    """
    view = MultiselectAjaxView.as_view()
    assert "joe" in regular_user.username

    results = _get_search_results(rf, view, "auth.User", "joe")
    assert len(results) == 1
    assert results[0].get("id") == regular_user.id
    assert results[0].get("name") == regular_user.username

    contact = PersonContact.objects.create(first_name="Joe", last_name="Somebody")

    results = _get_search_results(rf, view, "shuup.PersonContact", "joe")

    assert len(results) == 1
    assert results[0].get("id") == contact.id
    assert results[0].get("name") == contact.name

    contact.is_active = False
    contact.save()

    results = _get_search_results(rf, view, "shuup.PersonContact", "joe")

    assert len(results) == 0
