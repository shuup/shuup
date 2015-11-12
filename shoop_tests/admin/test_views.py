# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import json

import pytest
from shoop.testing.factories import (
    get_default_category, create_random_order, get_default_product,
    create_random_person, get_default_shop
)
from shoop.utils.importing import load
from shoop.testing.utils import apply_request_middleware


@pytest.mark.parametrize("class_spec", [
    "shoop.admin.modules.categories.views.list:CategoryListView",
    "shoop.admin.modules.contacts.views:ContactListView",
    "shoop.admin.modules.orders.views:OrderListView",
    "shoop.admin.modules.products.views:ProductListView",
])
@pytest.mark.django_db
def test_list_view(rf, class_spec):
    view = load(class_spec).as_view()
    request = rf.get("/", {
        "jq": json.dumps({"perPage": 100, "page": 1})
    })
    response = view(request)
    assert 200 <= response.status_code < 300


def random_order():
    # These are prerequisites for random orders
    contact = create_random_person()
    product = get_default_product()
    return create_random_order(contact, [product])


@pytest.mark.parametrize("model_and_class", [
    (get_default_category, "shoop.admin.modules.categories.views:CategoryEditView"),
    (create_random_person, "shoop.admin.modules.contacts.views:ContactDetailView"),
    (random_order, "shoop.admin.modules.orders.views:OrderDetailView"),
    (get_default_product, "shoop.admin.modules.products.views:ProductEditView"),
])
@pytest.mark.django_db
def test_detail_view(rf, admin_user, model_and_class):
    get_default_shop()  # obvious prerequisite
    model_func, class_spec = model_and_class
    model = model_func()
    view = load(class_spec).as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request, pk=model.pk)
    if hasattr(response, "render"):
        response.render()
    assert 200 <= response.status_code < 300
