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
from shuup.core.models import PersonContact
from shuup.customer_group_pricing.models import CgpDiscount, CgpPrice
from shuup.testing import factories


@pytest.mark.django_db
def test_product_catalog_discounted_price():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    contact = factories.create_random_person()
    group = PersonContact.get_default_group()
    contact.groups.add(group)
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("50"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("30"))

    # set price for product2
    CgpPrice.objects.create(shop=shop, product=product2, group=group, price_value=Decimal(25))
    # create a discount for product2
    CgpDiscount.objects.create(shop=shop, product=product2, group=group, discount_amount_value=Decimal(2))

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


@pytest.mark.django_db
def test_product_catalog_cgp_with_variations():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    contact = factories.create_random_person()
    group = PersonContact.get_default_group()
    contact.groups.add(group)
    parent = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("10"))
    child1 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("20"))
    child2 = factories.create_product("p3", shop=shop, supplier=supplier, default_price=Decimal("40"))
    child3 = factories.create_product("p4", shop=shop, supplier=supplier, default_price=Decimal("50"))

    child1.link_to_parent(parent)
    child2.link_to_parent(parent)
    child3.link_to_parent(parent)

    # set a price for child2
    CgpPrice.objects.create(shop=shop, product=child2, group=group, price_value=Decimal("5"))
    # create a discount for child3
    CgpDiscount.objects.create(shop=shop, product=child3, group=group, discount_amount_value=Decimal("35"))

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, contact=contact))
    ProductCatalog.index_product(parent)

    # return a Product queryset annotated with price and discounted price
    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    expected_prices = [
        (child2.pk, Decimal("5"), None),
        (child1.pk, Decimal("20"), None),
        (child3.pk, Decimal("50"), Decimal("15")),
    ]
    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert products_qs.count() == 3
    for index, value in enumerate(values):
        assert value == expected_prices[index]

    # return a ShopProduct queryset
    expected_prices = [
        (child2.get_shop_instance(shop).pk, Decimal("5"), None),
        (parent.get_shop_instance(shop).pk, Decimal("10"), None),
        (child1.get_shop_instance(shop).pk, Decimal("20"), None),
        (child3.get_shop_instance(shop).pk, Decimal("50"), Decimal("15")),
    ]
    shop_products_qs = catalog.get_shop_products_queryset().order_by("catalog_price")
    values = shop_products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert shop_products_qs.count() == 4
    for index, value in enumerate(values):
        assert value == expected_prices[index]
