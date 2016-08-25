# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core import cache
from shuup.core.models import Product, ProductMode, StockBehavior
from shuup.front.template_helpers import general
from shuup.testing.factories import (
    create_order_with_product, create_product, get_default_product,
    get_default_shop, get_default_supplier
)
from shuup.testing.mock_population import populate_if_required
from shuup_tests.front.fixtures import get_jinja_context
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
def test_get_root_categories():
    populate_if_required()
    context = get_jinja_context()
    for root in general.get_root_categories(context=context):
        assert not root.parent_id


@pytest.mark.django_db
def test_get_listed_products_orderable_only():
    context = get_jinja_context()
    shop = get_default_shop()
    simple_supplier = get_simple_supplier()
    n_products = 2

    # Create product without stock
    product = create_product(
        "test-sku",
        supplier=simple_supplier,
        shop=shop,
        stock_behavior=StockBehavior.STOCKED
    )
    assert len(general.get_listed_products(context, n_products, orderable_only=True)) == 0
    assert len(general.get_listed_products(context, n_products, orderable_only=False)) == 1

    # Increase stock on product
    quantity = product.get_shop_instance(shop).minimum_purchase_quantity
    simple_supplier.adjust_stock(product.id, quantity)
    assert len(general.get_listed_products(context, n_products, orderable_only=True)) == 1
    assert len(general.get_listed_products(context, n_products, orderable_only=False)) == 1

    # Decrease stock on product
    simple_supplier.adjust_stock(product.id, -quantity)
    assert len(general.get_listed_products(context, n_products, orderable_only=True)) == 0
    assert len(general.get_listed_products(context, n_products, orderable_only=False)) == 1


@pytest.mark.django_db
def test_get_listed_products_filter():
    context = get_jinja_context()
    shop = get_default_shop()
    supplier = get_default_supplier()

    product_1 = create_product(
        "test-sku-1",
        supplier=supplier,
        shop=shop,
    )
    product_2 = create_product(
        "test-sku-2",
        supplier=supplier,
        shop=shop,
    )
    filter_dict = {"id": product_1.id}
    product_list = general.get_listed_products(context, n_products=2, filter_dict=filter_dict)
    assert product_1 in product_list
    assert product_2 not in product_list

    # Test also with orderable_only False
    product_list = general.get_listed_products(context, n_products=2, filter_dict=filter_dict, orderable_only=False)
    assert product_1 in product_list
    assert product_2 not in product_list


@pytest.mark.django_db
def test_get_best_selling_products():
    context = get_jinja_context()
    cache.clear()
    # No products sold
    assert len(list(general.get_best_selling_products(context, n_products=2))) == 0

    supplier = get_default_supplier()
    shop = get_default_shop()
    product = get_default_product()
    create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=10, shop=shop)
    cache.clear()
    # One product sold
    assert len(list(general.get_best_selling_products(context, n_products=2))) == 1


@pytest.mark.django_db
def test_best_selling_products_with_multiple_orders():
    context = get_jinja_context()
    supplier = get_default_supplier()
    shop = get_default_shop()
    n_products = 2
    price = 10

    product_1 = create_product("test-sku-1", supplier=supplier, shop=shop)
    product_2 = create_product("test-sku-2", supplier=supplier, shop=shop)
    create_order_with_product(product_1, supplier, quantity=1, taxless_base_unit_price=price, shop=shop)
    create_order_with_product(product_2, supplier, quantity=1, taxless_base_unit_price=price, shop=shop)
    cache.clear()
    # Two initial products sold
    assert product_1 in general.get_best_selling_products(context, n_products=n_products)
    assert product_2 in general.get_best_selling_products(context, n_products=n_products)

    product_3 = create_product("test-sku-3", supplier=supplier, shop=shop)
    create_order_with_product(product_3, supplier, quantity=2, taxless_base_unit_price=price, shop=shop)
    cache.clear()
    # Third product sold in greater quantity
    assert product_3 in general.get_best_selling_products(context, n_products=n_products)

    create_order_with_product(product_1, supplier, quantity=4, taxless_base_unit_price=price, shop=shop)
    create_order_with_product(product_2, supplier, quantity=4, taxless_base_unit_price=price, shop=shop)
    cache.clear()
    # Third product outsold by first two products
    assert product_3 not in general.get_best_selling_products(context, n_products=n_products)


@pytest.mark.django_db
def test_get_newest_products():
    populate_if_required()
    context = get_jinja_context()
    assert len(list(general.get_newest_products(context, n_products=4))) == 4


@pytest.mark.django_db
def test_get_random_products():
    populate_if_required()
    context = get_jinja_context()
    assert len(list(general.get_random_products(context, n_products=4))) == 4


@pytest.mark.django_db
def test_get_all_manufacturers():
    populate_if_required()
    context = get_jinja_context()
    # TODO: This is not a good test
    assert len(general.get_all_manufacturers(context)) == 0


@pytest.mark.django_db
def test_get_pagination_variables():
    populate_if_required()  # Makes sure there is at least 30 products in db

    products = Product.objects.all()[:19]
    assert len(products) == 19
    vars = {"products": products}

    context = get_jinja_context(**vars)
    variables = general.get_pagination_variables(context, context["products"], limit=4)
    assert variables["page"].number == 1
    assert len(variables["objects"]) == 4

    context = get_jinja_context(path="/?page=5", **vars)
    variables = general.get_pagination_variables(context, context["products"], limit=4)
    assert variables["page"].number == 5
    assert len(variables["objects"]) == 3

    variables = general.get_pagination_variables(context, context["products"], limit=20)
    assert not variables["is_paginated"]
    assert variables["page"].number == 1

    context = get_jinja_context(path="/?page=42", **vars)
    variables = general.get_pagination_variables(context, context["products"], limit=4)
    assert variables["page"].number == 5
    assert len(variables["objects"]) == 3

    vars = {"products": []}
    context = get_jinja_context(path="/", **vars)
    variables = general.get_pagination_variables(context, context["products"], limit=4)
    assert not variables["is_paginated"]
