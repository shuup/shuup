# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

from shuup.core.models import PersonContact
from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.testing import factories
from shuup.customer_group_pricing.models import CgpDiscount, CgpPrice


def test_product_catalog_simple_list():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("30"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("10"))
    product3 = factories.create_product("p3", shop=shop, supplier=supplier, default_price=Decimal("20"))

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    ProductCatalog.index_product(product1)
    ProductCatalog.index_product(product2)
    ProductCatalog.index_product(product3)

    # return a Product queryset annotated with price and discounted price
    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    expected_prices = [
        (product2.pk, Decimal("10"), None),
        (product3.pk, Decimal("20"), None),
        (product1.pk, Decimal("30"), None),
    ]
    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert products_qs.count() == 3
    for index, value in enumerate(values):
        assert value == expected_prices[index]

    # return a ShopProduct queryset, annotated with price and discounted price
    expected_prices = [
        (product2.get_shop_instance(shop).pk, Decimal("10"), None),
        (product3.get_shop_instance(shop).pk, Decimal("20"), None),
        (product1.get_shop_instance(shop).pk, Decimal("30"), None),
    ]
    shop_products_qs = catalog.get_shop_products_queryset().order_by("catalog_price")
    values = shop_products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert shop_products_qs.count() == 3
    for index, value in enumerate(values):
        assert value == expected_prices[index]


def test_product_catalog_purchasable():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("30"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("10"))

    supplier.stock_managed = True
    supplier.save()

    # add 10 products to product1 stock
    supplier.adjust_stock(product1.pk, delta=10)

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=True))
    ProductCatalog.index_product(product1)
    ProductCatalog.index_product(product2)

    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    expected_prices = [(product1.pk, Decimal("30"), None)]
    assert products_qs.count() == 1

    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    for index, value in enumerate(values):
        assert value == expected_prices[index]

    shop_products_qs = catalog.get_shop_products_queryset().order_by("catalog_price")
    values = shop_products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    expected_prices = [(product1.get_shop_instance(shop).pk, Decimal("30"), None)]
    assert shop_products_qs.count() == 1
    for index, value in enumerate(values):
        assert value == expected_prices[index]


def test_product_catalog_variations():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    parent = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("10"))
    child1 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("20"))
    child2 = factories.create_product("p3", shop=shop, supplier=supplier, default_price=Decimal("40"))
    child3 = factories.create_product("p4", shop=shop, supplier=supplier, default_price=Decimal("50"))

    child1.link_to_parent(parent)
    child2.link_to_parent(parent)
    child3.link_to_parent(parent)

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    ProductCatalog.index_product(parent)

    # return a Product queryset annotated with price and discounted price
    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    expected_prices = [
        (child1.pk, Decimal("20"), None),
        (child2.pk, Decimal("40"), None),
        (child3.pk, Decimal("50"), None),
    ]
    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert products_qs.count() == 3
    for index, value in enumerate(values):
        assert value == expected_prices[index]

    # return a ShopProduct queryset
    expected_prices = [
        (parent.get_shop_instance(shop).pk, Decimal("10"), None),
        (child1.get_shop_instance(shop).pk, Decimal("20"), None),
        (child2.get_shop_instance(shop).pk, Decimal("40"), None),
        (child3.get_shop_instance(shop).pk, Decimal("50"), None),
    ]
    shop_products_qs = catalog.get_shop_products_queryset().order_by("catalog_price")
    values = shop_products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert shop_products_qs.count() == 4
    for index, value in enumerate(values):
        assert value == expected_prices[index]


def test_product_catalog_discounted_price():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    contact = factories.create_random_person()
    contact.groups.add(PersonContact.get_default_group())
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("50"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("30"))

    CgpPrice.objects.create(
        shop=shop, product=product2, group=PersonContact.get_default_group(), price_value=Decimal(25)
    )
    # create a discount for product2
    CgpDiscount.objects.create(
        shop=shop, product=product2, group=PersonContact.get_default_group(), discount_amount_value=Decimal(2)
    )

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, contact=contact))
    ProductCatalog.index_product(product1)
    ProductCatalog.index_product(product2)

    # return a Product queryset annotated with price and discounted price
    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    expected_prices = [
        (product2.pk, Decimal("25"), Decimal("23")),
        (product1.pk, Decimal("50"), None),
    ]
    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert products_qs.count() == 2
    for index, value in enumerate(values):
        assert value == expected_prices[index]

    # return a ShopProduct queryset, annotated with price and discounted price
    expected_prices = [
        (product2.get_shop_instance(shop).pk, Decimal("25"), Decimal("23")),
        (product1.get_shop_instance(shop).pk, Decimal("50"), None),
    ]
    shop_products_qs = catalog.get_shop_products_queryset().order_by("catalog_price")
    values = shop_products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert shop_products_qs.count() == 2
    for index, value in enumerate(values):
        assert value == expected_prices[index]
