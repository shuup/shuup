# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from django.core.management import call_command

from shuup.core.models import Product, ProductCrossSell, ShopProduct
from shuup.core.utils.product_bought_with_relations import add_bought_with_relations_for_product
from shuup.testing.factories import (
    add_product_to_order,
    create_order_with_product,
    create_product,
    get_default_shop,
    get_default_supplier,
)


@pytest.mark.django_db
def test_computing_simple_product_relations(rf):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    related_product = create_product("simple-related-product", shop)
    quantities = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    for quantity in quantities:
        order = create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=6, shop=shop)
        add_product_to_order(order, supplier, related_product, quantity=quantity, taxless_base_unit_price=6)

    assert ProductCrossSell.objects.count() == 0
    add_bought_with_relations_for_product(product.pk)
    assert ProductCrossSell.objects.count() == 1
    cross_sell_product = ProductCrossSell.objects.filter(product1=product).first()
    assert cross_sell_product.product2 == related_product
    assert cross_sell_product.weight == sum(quantities)

    add_bought_with_relations_for_product(related_product.id)
    assert ProductCrossSell.objects.count() == 2
    cross_sell_product = ProductCrossSell.objects.filter(product1=related_product).first()
    assert cross_sell_product.product2 == product
    assert cross_sell_product.weight == len(quantities)


@pytest.mark.django_db
def test_product_relations_max_quantity(rf):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    quantities = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    for i, quantity in enumerate(quantities):
        order = create_order_with_product(product, supplier, quantity=1, taxless_base_unit_price=6, shop=shop)
        add_product_to_order(
            order, supplier, create_product("product-%s" % i, shop), quantity=quantity, taxless_base_unit_price=6
        )

    assert ProductCrossSell.objects.count() == 0
    add_bought_with_relations_for_product(product.pk, max_quantity=5)
    assert ProductCrossSell.objects.count() == 5
    # Test that ordering is ok
    assert not ProductCrossSell.objects.filter(weight=1).exists()
    assert ProductCrossSell.objects.filter(weight=11).exists()


def _init_test_with_variations():
    shop = get_default_shop()
    supplier = get_default_supplier()

    product_data = {
        "t-shirt": {
            "colors": ["black", "yellow"],
        },
        "hoodie": {
            "colors": ["black"],
        },
    }
    for key, data in six.iteritems(product_data):
        parent = create_product(key, shop=shop)
        shop_parent_product = parent.get_shop_instance(shop)
        for color in data["colors"]:
            sku = "%s-%s" % (key, color)
            shop_product = ShopProduct.objects.filter(product__sku=sku).first()
            if shop_product:
                shop_product.suppliers.add(supplier)
            else:
                child = create_product(sku, shop=shop, supplier=supplier)
                child.link_to_parent(parent, variables={"color": color})

    assert Product.objects.count() == 5

    black_t_shirt = Product.objects.filter(sku="t-shirt-black").first()
    black_hoodie = Product.objects.filter(sku="hoodie-black").first()
    order = create_order_with_product(black_t_shirt, supplier, quantity=1, taxless_base_unit_price=6, shop=shop)
    add_product_to_order(order, supplier, black_hoodie, quantity=1, taxless_base_unit_price=6)

    return black_t_shirt, black_hoodie


@pytest.mark.django_db
def test_product_relations_variation_products(rf):
    t_shirt, hoodie = _init_test_with_variations()

    add_bought_with_relations_for_product(t_shirt.pk)

    # T-shirt should be related to hoodie parent product
    assert ProductCrossSell.objects.count() == 1
    t_shirt_relation = ProductCrossSell.objects.filter(product2=hoodie).first()
    assert t_shirt_relation
    assert t_shirt_relation.product1 == t_shirt

    add_bought_with_relations_for_product(hoodie.pk)
    assert ProductCrossSell.objects.count() == 2

    # Hoodie should be related to t-shirt product
    hoodie_relation = ProductCrossSell.objects.filter(product2=t_shirt).first()
    assert hoodie_relation
    assert hoodie_relation.product1 == hoodie


@pytest.mark.django_db
def test_product_relations_variation_products_through_management_cmd(rf):
    t_shirt, hoodie = _init_test_with_variations()
    call_command("compute_bought_with_relations")

    assert ProductCrossSell.objects.count() == 2
    t_shirt_relation = ProductCrossSell.objects.filter(product2=hoodie).first()
    assert t_shirt_relation
    assert t_shirt_relation.product1 == t_shirt

    hoodie_relation = ProductCrossSell.objects.filter(product2=t_shirt).first()
    assert hoodie_relation
    assert hoodie_relation.product1 == hoodie
