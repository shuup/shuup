# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import pytz
from datetime import datetime, time, timedelta
from decimal import Decimal
from django.utils import timezone
from mock import patch

from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import AnonymousContact, PersonContact
from shuup.core.pricing import PricingContext
from shuup.discounts.models import Discount, HappyHour, TimeRange
from shuup.testing import factories


@pytest.mark.django_db
def test_product_catalog_category_discount():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    contact = factories.create_random_person()
    group = PersonContact.get_default_group()
    category = factories.get_default_category()
    contact.groups.add(group)
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("10"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("20"))
    product3 = factories.create_product("p3", shop=shop, supplier=supplier, default_price=Decimal("30"))
    product1.get_shop_instance(shop).categories.add(category)
    product3.get_shop_instance(shop).categories.add(category)

    # create a 10% discount for the category
    Discount.objects.create(
        shop=shop,
        category=category,
        discount_percentage=Decimal(0.1),
        start_datetime=timezone.now(),
        end_datetime=timezone.now() + timedelta(days=1),
    )

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    ProductCatalog.index_product(product1)
    ProductCatalog.index_product(product2)
    ProductCatalog.index_product(product3)

    _assert_products_queryset(
        catalog,
        [
            (product1.pk, Decimal("10"), Decimal("9")),
            (product2.pk, Decimal("20"), None),
            (product3.pk, Decimal("30"), Decimal("27")),
        ],
    )
    _assert_shop_products_queryset(
        catalog,
        [
            (product1.get_shop_instance(shop).pk, Decimal("10"), Decimal("9")),
            (product2.get_shop_instance(shop).pk, Decimal("20"), None),
            (product3.get_shop_instance(shop).pk, Decimal("30"), Decimal("27")),
        ],
    )
    _assert_price(product1, shop, Decimal("9"), Decimal("10"))
    _assert_price(product2, shop, Decimal("20"), Decimal("20"))
    _assert_price(product3, shop, Decimal("27"), Decimal("30"))


@pytest.mark.django_db
def test_product_catalog_product_discount():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("10"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("20"))

    # create a $5 discount for the product
    Discount.objects.create(
        shop=shop,
        product=product1,
        discount_amount_value=Decimal(5),
        start_datetime=timezone.now(),
        end_datetime=timezone.now() + timedelta(days=1),
    )

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    ProductCatalog.index_product(product1)
    ProductCatalog.index_product(product2)

    _assert_products_queryset(
        catalog,
        [
            (product1.pk, Decimal("10"), Decimal("5")),
            (product2.pk, Decimal("20"), None),
        ],
    )
    _assert_shop_products_queryset(
        catalog,
        [
            (product1.get_shop_instance(shop).pk, Decimal("10"), Decimal("5")),
            (product2.get_shop_instance(shop).pk, Decimal("20"), None),
        ],
    )
    _assert_price(product1, shop, Decimal("5"), Decimal("10"))
    _assert_price(product2, shop, Decimal("20"), Decimal("20"))


@pytest.mark.django_db
def test_product_catalog_happy_hour_discount():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("10"))
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=Decimal("20"))

    # create a 20% discount for a happy hour (should be in range of 8pm-9pm)
    discount = Discount.objects.create(
        shop=shop,
        discount_percentage=Decimal(0.2),
        start_datetime=datetime(2021, 1, 1, tzinfo=pytz.utc),
        end_datetime=datetime(2021, 1, 30, tzinfo=pytz.utc),
    )
    happy_hour = HappyHour.objects.create(name="Super Happy", shop=shop)
    # the happy hour is on Mondays from 8-9pm
    TimeRange.objects.create(from_hour=time(20, 0), to_hour=time(21, 0), weekday=0, happy_hour=happy_hour)
    discount.happy_hours.add(happy_hour)

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    ProductCatalog.index_product(product1)
    ProductCatalog.index_product(product2)

    # Monday, 12pm
    with patch.object(timezone, "now", return_value=datetime(2021, 1, 4, 12, 0, tzinfo=pytz.utc)):
        _assert_products_queryset(
            catalog,
            [
                (product1.pk, Decimal("10"), None),
                (product2.pk, Decimal("20"), None),
            ],
        )
        _assert_shop_products_queryset(
            catalog,
            [
                (product1.get_shop_instance(shop).pk, Decimal("10"), None),
                (product2.get_shop_instance(shop).pk, Decimal("20"), None),
            ],
        )
        _assert_price(product1, shop, Decimal("10"), Decimal("10"))
        _assert_price(product2, shop, Decimal("20"), Decimal("20"))

    # Monday, 8:30pm
    with patch.object(timezone, "now", return_value=datetime(2021, 1, 4, 20, 30, tzinfo=pytz.utc)):
        _assert_products_queryset(
            catalog,
            [
                (product1.pk, Decimal("10"), Decimal("8")),
                (product2.pk, Decimal("20"), Decimal("16")),
            ],
        )
        _assert_shop_products_queryset(
            catalog,
            [
                (product1.get_shop_instance(shop).pk, Decimal("10"), Decimal("8")),
                (product2.get_shop_instance(shop).pk, Decimal("20"), Decimal("16")),
            ],
        )
        _assert_price(product1, shop, Decimal("8"), Decimal("10"))
        _assert_price(product2, shop, Decimal("16"), Decimal("20"))


@pytest.mark.django_db
def test_product_catalog_happy_hour_timezone_discount():
    """
    Make sure a discount is valid for different timezones
    """
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    product1 = factories.create_product("p1", shop=shop, supplier=supplier, default_price=Decimal("10"))

    discount = Discount.objects.create(
        shop=shop,
        discount_percentage=Decimal(0.1),
        start_datetime=datetime(2021, 1, 1, tzinfo=pytz.utc),
        end_datetime=datetime(2021, 1, 30, tzinfo=pytz.utc),
    )
    happy_hour = HappyHour.objects.create(name="Super Happy", shop=shop)
    # the happy hour is available on Mondays, from 2am-4am (UTC)
    TimeRange.objects.create(from_hour=time(2, 0), to_hour=time(4, 0), weekday=0, happy_hour=happy_hour)
    discount.happy_hours.add(happy_hour)

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    ProductCatalog.index_product(product1)

    # Monday, 2am UTC - valid discounts
    with patch.object(timezone, "now", return_value=datetime(2021, 1, 4, 2, 0, tzinfo=pytz.utc)):
        _assert_price(product1, shop, Decimal("9"), Decimal("10"))
        _assert_products_queryset(catalog, [(product1.pk, Decimal("10"), Decimal("9"))])

    # it's Monday, 11:58pm in Brazil, the discount shouldn't be valid
    sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
    with patch.object(timezone, "now", return_value=sao_paulo_tz.localize(datetime(2021, 1, 4, 23, 58))):
        _assert_price(product1, shop, Decimal("10"), Decimal("10"))
        _assert_products_queryset(catalog, [(product1.pk, Decimal("10"), None)])

    # it's Monday, 2:58am in Brazil on Monday, the discount shouldn't be valid
    with patch.object(timezone, "now", return_value=sao_paulo_tz.localize(datetime(2021, 1, 4, 2, 58))):
        _assert_price(product1, shop, Decimal("10"), Decimal("10"))
        _assert_products_queryset(catalog, [(product1.pk, Decimal("10"), None)])

    # it's Sunday, 11:58pm in Brazil, the discount should be available as it is Monday 2:58am in UTC
    with patch.object(timezone, "now", return_value=sao_paulo_tz.localize(datetime(2021, 1, 3, 23, 58))):
        _assert_price(product1, shop, Decimal("9"), Decimal("10"))
        _assert_products_queryset(catalog, [(product1.pk, Decimal("10"), Decimal("9"))])


def _assert_price(product, shop, expected_price, expected_base_price):
    context = PricingContext(shop=shop, customer=AnonymousContact())
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
