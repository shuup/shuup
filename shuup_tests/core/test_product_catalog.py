# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal

from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import AnonymousContact, ProductVisibility, ShopProduct, ShopProductVisibility
from shuup.core.pricing import PricingContext
from shuup.testing import factories


@pytest.mark.django_db
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

    _assert_products_queryset(
        catalog,
        [
            (product2.pk, Decimal("10"), None),
            (product3.pk, Decimal("20"), None),
            (product1.pk, Decimal("30"), None),
        ],
    )
    _assert_shop_products_queryset(
        catalog,
        [
            (product2.get_shop_instance(shop).pk, Decimal("10"), None),
            (product3.get_shop_instance(shop).pk, Decimal("20"), None),
            (product1.get_shop_instance(shop).pk, Decimal("30"), None),
        ],
    )
    _assert_price(product1, shop, Decimal("30"), Decimal("30"))
    _assert_price(product2, shop, Decimal("10"), Decimal("10"))
    _assert_price(product3, shop, Decimal("20"), Decimal("20"))


@pytest.mark.django_db
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

    _assert_products_queryset(catalog, [(product1.pk, Decimal("30"), None)])
    _assert_shop_products_queryset(catalog, [(product1.get_shop_instance(shop).pk, Decimal("30"), None)])


@pytest.mark.django_db
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

    _assert_products_queryset(
        catalog,
        [
            (parent.pk, Decimal("10"), None),
            (child1.pk, Decimal("20"), None),
            (child2.pk, Decimal("40"), None),
            (child3.pk, Decimal("50"), None),
        ],
    )
    _assert_shop_products_queryset(
        catalog,
        [
            (parent.get_shop_instance(shop).pk, Decimal("10"), None),
            (child1.get_shop_instance(shop).pk, Decimal("20"), None),
            (child2.get_shop_instance(shop).pk, Decimal("40"), None),
            (child3.get_shop_instance(shop).pk, Decimal("50"), None),
        ],
    )
    _assert_price(parent, shop, Decimal("10"), Decimal("10"))
    _assert_price(child1, shop, Decimal("20"), Decimal("20"))
    _assert_price(child2, shop, Decimal("40"), Decimal("40"))
    _assert_price(child3, shop, Decimal("50"), Decimal("50"))


@pytest.mark.django_db
def test_product_catalog_availability():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("30"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("10"))

    supplier.stock_managed = True
    supplier.save()

    # add 10 products to product1 stock
    supplier.adjust_stock(product1.pk, delta=10)

    catalog_available_only = ProductCatalog(context=ProductCatalogContext(purchasable_only=True))
    catalog_visible_only = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    catalog_all = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, visible_only=False))
    ProductCatalog.index_product(product1)
    ProductCatalog.index_product(product2)

    assert catalog_available_only.get_products_queryset().count() == 1
    assert catalog_visible_only.get_products_queryset().count() == 2
    assert catalog_all.get_products_queryset().count() == 2

    # change the product1 visibility
    ShopProduct.objects.all().update(visibility=ShopProductVisibility.NOT_VISIBLE)
    ProductCatalog.index_product(product1)
    ProductCatalog.index_product(product2)

    assert catalog_available_only.get_products_queryset().count() == 0
    assert catalog_visible_only.get_products_queryset().count() == 0
    assert catalog_all.get_products_queryset().count() == 2


@pytest.mark.django_db
def test_product_catalog_visibilities():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    contact = factories.create_random_person()
    group = factories.create_random_contact_group(shop)
    contact.groups.add(group)
    product = factories.create_product("p", shop=shop, supplier=supplier, default_price=Decimal("10"))

    catalog_visible_only = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    catalog_visible_contact = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, contact=contact))
    catalog_all = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, visible_only=False))
    ProductCatalog.index_product(product)

    assert catalog_visible_only.get_products_queryset().count() == 1
    assert catalog_visible_contact.get_products_queryset().count() == 1
    assert catalog_all.get_products_queryset().count() == 1

    # change the visibility to groups
    shop_product = product.get_shop_instance(shop)
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_GROUPS
    shop_product.save()
    shop_product.visibility_groups.add(group)
    ProductCatalog.index_product(product)

    assert catalog_visible_only.get_products_queryset().count() == 0
    assert catalog_visible_contact.get_products_queryset().count() == 1
    assert catalog_all.get_products_queryset().count() == 1

    # change the visibility to logged in
    shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_LOGGED_IN
    shop_product.save()
    ProductCatalog.index_product(product)

    assert catalog_visible_only.get_products_queryset().count() == 0
    assert catalog_visible_contact.get_products_queryset().count() == 1
    assert catalog_all.get_products_queryset().count() == 1


def _assert_price(product, shop, expected_price, expected_base_price, customer=None):
    context = PricingContext(shop=shop, customer=customer or AnonymousContact())
    price = product.get_price_info(context)
    assert price.price.value == expected_price
    assert price.base_price.value == expected_base_price


def _assert_products_queryset(catalog, expected_prices):
    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert products_qs.count() == len(expected_prices)
    for index, value in enumerate(values):
        assert value == expected_prices[index]


def _assert_shop_products_queryset(catalog, expected_prices):
    shop_products_qs = catalog.get_shop_products_queryset().order_by("catalog_price")
    values = shop_products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert shop_products_qs.count() == len(expected_prices)
    for index, value in enumerate(values):
        assert value == expected_prices[index]
