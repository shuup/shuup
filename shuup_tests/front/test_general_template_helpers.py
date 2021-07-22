# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core import cache
from shuup.core.models import AnonymousContact, Manufacturer, Product, ShopProductVisibility, Supplier
from shuup.front.apps.auth.forms import EmailAuthenticationForm
from shuup.testing.factories import (
    create_order_with_product,
    create_product,
    get_default_category,
    get_default_shop,
    get_default_supplier,
    get_supplier,
)
from shuup.testing.mock_population import populate_if_required
from shuup.testing.utils import apply_request_middleware
from shuup_tests.front.fixtures import get_jinja_context
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
def test_get_login_form(rf):
    from shuup.front.template_helpers import general

    request = apply_request_middleware(rf.get("/"), shop=get_default_shop())
    form = general.get_login_form(request=request)
    assert isinstance(form, EmailAuthenticationForm)


@pytest.mark.django_db
def test_get_root_categories():
    populate_if_required()
    context = get_jinja_context()
    from shuup.front.template_helpers import general

    for root in general.get_root_categories(context=context):
        assert not root.parent_id


@pytest.mark.django_db
def test_get_listed_products_orderable_only(reindex_catalog):
    context = get_jinja_context()
    shop = get_default_shop()
    simple_supplier = get_simple_supplier()
    n_products = 2

    # Create product without stock
    product = create_product("test-sku", supplier=simple_supplier, shop=shop)

    create_product("test-sku-2", supplier=simple_supplier, shop=shop)
    create_product("test-sku-3", supplier=simple_supplier, shop=shop)
    create_product("test-sku-4", supplier=simple_supplier, shop=shop)

    reindex_catalog()

    from shuup.front.template_helpers import general

    assert len(general.get_listed_products(context, n_products, orderable_only=True)) == 0
    assert len(general.get_listed_products(context, n_products, orderable_only=False)) == 2

    # Increase stock on product
    quantity = product.get_shop_instance(shop).minimum_purchase_quantity
    simple_supplier.adjust_stock(product.id, quantity)
    reindex_catalog()

    assert len(general.get_listed_products(context, n_products, orderable_only=True)) == 1
    assert len(general.get_listed_products(context, n_products, orderable_only=False)) == 2

    # Decrease stock on product
    simple_supplier.adjust_stock(product.id, -quantity)
    reindex_catalog()

    assert len(general.get_listed_products(context, n_products, orderable_only=True)) == 0
    assert len(general.get_listed_products(context, n_products, orderable_only=False)) == 2


@pytest.mark.django_db
def test_get_listed_products_filter(reindex_catalog):
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
    reindex_catalog()

    from shuup.front.template_helpers import general

    filter_dict = {"id": product_1.id}
    product_list = general.get_listed_products(context, n_products=2, filter_dict=filter_dict)
    assert product_1 in product_list
    assert product_2 not in product_list

    product_list = general.get_listed_products(context, n_products=2, filter_dict=filter_dict, orderable_only=False)
    assert product_1 in product_list
    assert product_2 not in product_list


@pytest.mark.django_db
def test_get_best_selling_products(reindex_catalog):
    from shuup.front.template_helpers import general

    context = get_jinja_context()
    reindex_catalog()

    # No products sold
    assert len(list(general.get_best_selling_products(context, n_products=3))) == 0
    shop = get_default_shop()

    supplier = get_default_supplier()
    supplier2 = Supplier.objects.create(name="supplier2", enabled=True)
    supplier3 = Supplier.objects.create(name="supplier3", enabled=True)
    supplier2.shops.add(shop)
    supplier3.shops.add(shop)

    product1 = create_product("product1", shop, supplier, 10)
    product2 = create_product("product2", shop, supplier, 20)
    create_order_with_product(product1, supplier, quantity=1, taxless_base_unit_price=10, shop=shop)
    create_order_with_product(product2, supplier, quantity=2, taxless_base_unit_price=20, shop=shop)

    reindex_catalog()
    cache.clear()

    # Two products sold
    best_selling_products = list(general.get_best_selling_products(context, n_products=3))
    assert len(best_selling_products) == 2
    assert product1 in best_selling_products
    assert product2 in best_selling_products

    # Make order unorderable
    shop_product = product1.get_shop_instance(shop)
    shop_product.visibility = ShopProductVisibility.NOT_VISIBLE
    shop_product.save()

    reindex_catalog()
    cache.clear()

    best_selling_products = list(general.get_best_selling_products(context, n_products=3))
    assert len(best_selling_products) == 1
    assert product1 not in best_selling_products
    assert product2 in best_selling_products

    # add a new product with discounted amount
    product3 = create_product("product3", supplier=supplier, shop=shop, default_price=30)
    create_order_with_product(product3, supplier, quantity=1, taxless_base_unit_price=30, shop=shop)

    reindex_catalog()

    from shuup.customer_group_pricing.models import CgpDiscount

    CgpDiscount.objects.create(
        shop=shop, product=product3, group=AnonymousContact.get_default_group(), discount_amount_value=5
    )
    reindex_catalog()
    cache.clear()

    best_selling_products = list(general.get_best_selling_products(context, n_products=3, orderable_only=True))
    assert len(best_selling_products) == 2
    assert product1 not in best_selling_products
    assert product2 in best_selling_products
    assert product3 in best_selling_products


@pytest.mark.django_db
def test_get_best_selling_products_per_supplier(reindex_catalog):
    from shuup.front.template_helpers import general

    context = get_jinja_context()

    reindex_catalog()

    # No products sold
    assert len(list(general.get_best_selling_products(context, n_products=3))) == 0
    shop = get_default_shop()

    supplier = get_supplier("simple_supplier", shop, name="Supplier 1")
    supplier2 = get_supplier("simple_supplier", shop, name="Supplier 2")

    product1 = create_product("product1", shop, supplier, 10)
    product2 = create_product("product2", shop, supplier2, 20)
    create_order_with_product(product1, supplier, quantity=1, taxless_base_unit_price=10, shop=shop)
    create_order_with_product(product2, supplier2, quantity=2, taxless_base_unit_price=20, shop=shop)

    reindex_catalog()

    # Two products sold, but only one supplier
    best_selling_products = list(general.get_best_selling_products(context, n_products=3, supplier=supplier))
    assert len(best_selling_products) == 1
    assert product1 in best_selling_products
    assert product2 not in best_selling_products

    # Two products sold, but only one supplier
    cache.clear()
    best_selling_products = list(general.get_best_selling_products(context, n_products=3, supplier=supplier2))
    assert len(best_selling_products) == 1
    assert product1 not in best_selling_products
    assert product2 in best_selling_products

    # Make product 1 also sold by supplier2
    shop_product = product1.get_shop_instance(shop)
    shop_product.suppliers.add(supplier2)

    reindex_catalog()

    cache.clear()
    best_selling_products = list(general.get_best_selling_products(context, n_products=3, supplier=supplier2))
    assert len(best_selling_products) == 1  # Since there isn't any orders yet for supplier 2
    assert product2 in best_selling_products

    # get for all suppliers
    cache.clear()
    best_selling_products = list(general.get_best_selling_products(context, n_products=3))
    assert len(best_selling_products) == 2
    assert product1 in best_selling_products
    assert product2 in best_selling_products


@pytest.mark.django_db
def test_best_selling_products_with_multiple_orders(reindex_catalog):
    from shuup.front.template_helpers import general

    context = get_jinja_context()
    supplier = get_default_supplier()
    shop = get_default_shop()
    n_products = 2
    price = 10

    product_1 = create_product("test-sku-1", supplier=supplier, shop=shop, default_price=price)
    product_2 = create_product("test-sku-2", supplier=supplier, shop=shop, default_price=price)
    create_order_with_product(product_1, supplier, quantity=1, taxless_base_unit_price=price, shop=shop)
    create_order_with_product(product_2, supplier, quantity=1, taxless_base_unit_price=price, shop=shop)

    reindex_catalog()
    cache.clear()

    # Two initial products sold
    assert product_1 in general.get_best_selling_products(context, n_products=n_products)
    assert product_2 in general.get_best_selling_products(context, n_products=n_products)

    product_3 = create_product("test-sku-3", supplier=supplier, shop=shop, default_price=price)
    create_order_with_product(product_3, supplier, quantity=2, taxless_base_unit_price=price, shop=shop)

    reindex_catalog()
    cache.clear()

    # Third product sold in greater quantity
    assert product_3 in general.get_best_selling_products(context, n_products=n_products)

    create_order_with_product(product_1, supplier, quantity=4, taxless_base_unit_price=price, shop=shop)
    create_order_with_product(product_2, supplier, quantity=4, taxless_base_unit_price=price, shop=shop)

    reindex_catalog()
    cache.clear()

    # Third product outsold by first two products
    assert product_3 not in general.get_best_selling_products(context, n_products=n_products)

    children = [create_product("SimpleVarChild-%d" % x, supplier=supplier, shop=shop) for x in range(5)]
    for child in children:
        child.link_to_parent(product_3)
        create_order_with_product(child, supplier, quantity=1, taxless_base_unit_price=price, shop=shop)

    reindex_catalog()
    cache.clear()

    # Third product now sold in greatest quantity
    assert product_3 == general.get_best_selling_products(context, n_products=n_products)[0]

    # add a new product with discounted amount
    product_4 = create_product("test-sku-4", supplier=supplier, shop=shop, default_price=price)
    create_order_with_product(product_4, supplier, quantity=20, taxless_base_unit_price=price, shop=shop)
    from shuup.customer_group_pricing.models import CgpDiscount

    CgpDiscount.objects.create(
        shop=shop, product=product_4, group=AnonymousContact.get_default_group(), discount_amount_value=(price * 0.1)
    )

    reindex_catalog()
    cache.clear()

    assert product_4 == general.get_best_selling_products(context, n_products=n_products)[0]


@pytest.mark.django_db
def test_get_newest_products(reindex_catalog):
    from shuup.front.template_helpers import general

    supplier = get_default_supplier()
    shop = get_default_shop()
    products = [create_product("sku-%d" % x, supplier=supplier, shop=shop, default_price=x + 1) for x in range(2)]
    children = [
        create_product("SimpleVarChild-%d" % x, supplier=supplier, shop=shop, default_price=x + 1) for x in range(2)
    ]

    for child in children:
        child.link_to_parent(products[0])

    reindex_catalog()

    context = get_jinja_context()
    newest_products = list(general.get_newest_products(context, n_products=10))

    # only 2 products exist
    assert len(newest_products) == 2
    assert products[0] in newest_products
    assert products[1] in newest_products

    # Delete one product
    products[0].soft_delete()
    reindex_catalog()

    newest_products = list(general.get_newest_products(context, n_products=10))
    # only 2 products exist
    assert len(newest_products) == 1
    assert products[0] not in newest_products
    assert products[1] in newest_products


@pytest.mark.django_db
def test_get_random_products(reindex_catalog):
    from shuup.front.template_helpers import general

    supplier = get_default_supplier()
    shop = get_default_shop()

    products = [create_product("sku-%d" % x, supplier=supplier, shop=shop) for x in range(2)]
    children = [create_product("SimpleVarChild-%d" % x, supplier=supplier, shop=shop) for x in range(2)]

    for child in children:
        child.link_to_parent(products[0])

    reindex_catalog()

    context = get_jinja_context()
    random_products = list(general.get_random_products(context, n_products=10))
    assert len(random_products) == 2

    # only 2 parent products exist
    assert products[0] in random_products
    assert products[1] in random_products


@pytest.mark.django_db
def test_products_for_category(reindex_catalog):
    from shuup.front.template_helpers import general

    supplier = get_default_supplier()
    shop = get_default_shop()

    category = get_default_category()
    products = [create_product("sku-%d" % x, supplier=supplier, shop=shop) for x in range(2)]
    children = [create_product("SimpleVarChild-%d" % x, supplier=supplier, shop=shop) for x in range(2)]
    category.shops.add(shop)

    for child in children:
        child.link_to_parent(products[0])

    reindex_catalog()

    context = get_jinja_context()

    for product in products:
        product.get_shop_instance(shop).categories.add(category)

    reindex_catalog()

    category_products = list(general.get_products_for_categories(context, [category]))
    assert len(category_products) == 2
    assert products[0] in category_products
    assert products[1] in category_products


@pytest.mark.django_db
def test_get_all_manufacturers(reindex_catalog):
    from shuup.front.template_helpers import general

    context = get_jinja_context()
    supplier = get_default_supplier()
    shop = get_default_shop()
    manuf1 = Manufacturer.objects.create(name="M1")
    manuf2 = Manufacturer.objects.create(name="M2")
    manuf3 = Manufacturer.objects.create(name="M2")
    manuf1.shops.add(shop)
    manuf2.shops.add(shop)

    products = [create_product("sku-%d" % x, supplier=supplier, shop=shop) for x in range(3)]
    products[0].manufacturer = manuf1
    products[0].save()
    products[1].manufacturer = manuf2
    products[1].save()
    products[2].manufacturer = manuf3
    products[2].save()

    reindex_catalog()

    assert len(general.get_all_manufacturers(context)) == 3


@pytest.mark.django_db
def test_get_pagination_variables(reindex_catalog):
    from shuup.front.template_helpers import general

    populate_if_required()  # Makes sure there is at least 30 products in db

    products = Product.objects.all()[:19]
    assert len(products) == 19
    vars = {"products": products}

    reindex_catalog()

    context = get_jinja_context(**vars)
    variables = general.get_pagination_variables(context, context["products"], limit=2)
    assert variables["page"].number == 1
    assert len(variables["objects"]) == 2
    assert variables["page_range"][0] == 1
    assert variables["page_range"][-1] == 5

    context = get_jinja_context(path="/?page=5", **vars)
    variables = general.get_pagination_variables(context, context["products"], limit=2)
    assert variables["page"].number == 5
    assert len(variables["objects"]) == 2
    assert variables["page_range"][0] == 3
    assert variables["page_range"][-1] == 7

    variables = general.get_pagination_variables(context, context["products"], limit=20)
    assert not variables["is_paginated"]
    assert variables["page"].number == 1
    assert variables["page_range"][0] == variables["page_range"][-1] == 1

    context = get_jinja_context(path="/?page=42", **vars)
    variables = general.get_pagination_variables(context, context["products"], limit=4)
    assert variables["page"].number == 5
    assert len(variables["objects"]) == 3
    assert variables["page_range"][0] == 1
    assert variables["page_range"][-1] == 5

    vars = {"products": []}
    context = get_jinja_context(path="/", **vars)
    variables = general.get_pagination_variables(context, context["products"], limit=4)
    assert not variables["is_paginated"]
    assert variables["page_range"][0] == variables["page_range"][-1] == 1
