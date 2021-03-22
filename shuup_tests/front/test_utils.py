# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core import cache
from shuup.core.models import Product, ProductVariationVariable, ProductVariationVariableValue, ShopProduct
from shuup.front.utils.product import get_orderable_variation_children
from shuup.front.utils.sorts_and_filters import get_product_queryset
from shuup.front.utils.user import is_admin_user
from shuup.testing.factories import create_product, get_default_shop, get_default_supplier
from shuup.testing.utils import apply_request_middleware
from shuup_tests.front.fixtures import get_jinja_context
from shuup_tests.utils.fixtures import regular_user


@pytest.mark.django_db
def test_get_sorts_and_filters(rf):
    context = get_jinja_context()

    supplier = get_default_supplier()
    shop = get_default_shop()
    product1 = create_product("product1", shop, supplier, 10)
    product2 = create_product("product2", shop, supplier, 20)

    request = apply_request_middleware(rf.get("/"))
    queryset = Product.objects.all()

    cache.clear()
    for time in range(2):
        products = list(get_product_queryset(queryset, request, None, {}))
        assert len(products) == 2
        assert product1 in products
        assert product2 in products


@pytest.mark.django_db
def test_get_orderable_variation_children(rf):
    supplier = get_default_supplier()
    shop = get_default_shop()

    variable_name = "Color"
    parent = create_product("test-sku-1", shop=shop)
    variation_variable = ProductVariationVariable.objects.create(product=parent, identifier="color", name=variable_name)
    red_value = ProductVariationVariableValue.objects.create(variable=variation_variable, identifier="red", value="Red")
    blue_value = ProductVariationVariableValue.objects.create(
        variable=variation_variable, identifier="blue", value="Blue"
    )
    combinations = list(parent.get_all_available_combinations())
    assert len(combinations) == 2
    for combo in combinations:
        assert not combo["result_product_pk"]
        child = create_product(
            "xyz-%s" % combo["sku_part"], shop=shop, supplier=get_default_supplier(), default_price=20
        )
        child.link_to_parent(parent, combination_hash=combo["hash"])

    combinations = list(parent.get_all_available_combinations())
    assert len(combinations) == 2
    parent.refresh_from_db()
    assert parent.is_variation_parent()
    request = apply_request_middleware(rf.get("/"))

    cache.clear()
    for time in range(2):
        orderable_children, is_orderable = get_orderable_variation_children(parent, request, None)
        assert len(orderable_children)
        for var_variable, var_values in dict(orderable_children).items():
            assert var_variable == variation_variable
            assert red_value in var_values
            assert blue_value in var_values


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_is_admin_user_func(rf, admin_user, regular_user):
    get_default_shop()
    regular_user.is_staff = True
    request = apply_request_middleware(rf.post("/"), user=regular_user)
    assert not is_admin_user(request)
    assert not request.is_admin_user
    assert not is_admin_user(request)

    request = apply_request_middleware(rf.post("/"), user=admin_user)
    assert is_admin_user(request)
    assert request.is_admin_user
    assert is_admin_user(request)

    request = apply_request_middleware(rf.post("/"))
    assert not is_admin_user(request)
