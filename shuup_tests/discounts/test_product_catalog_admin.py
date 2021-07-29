# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytz
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from mock import patch

from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import PersonContact
from shuup.discounts.admin.views import DiscountEditView, HappyHourEditView
from shuup.discounts.models import Discount, HappyHour
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import atomic_commit_mock


def _init_test():
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    contact = factories.create_random_person()
    group = PersonContact.get_default_group()
    category = factories.get_default_category()
    contact.groups.add(group)
    return shop, supplier, contact, group, category


def _get_default_discount_data(overrides={}):
    data = {
        "name": "My Discount",
        "active": "on",
        "start_datetime": timezone.now().strftime("%Y-%m-%d %H:%M"),
        "end_datetime": (timezone.now() + timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
        "product": "",
        "category": "",
        "contact": "",
        "contact_group": "",
        "supplier": "",
        "discount_amount_value": "",
        "discounted_price_value": "",
        "discount_percentage": "",
    }
    if overrides:
        data.update(overrides)
    return data


def test_admin_catalog_discount_product_filter(rf, admin_user):
    shop, supplier, contact, group, category = _init_test()
    default_price = Decimal("15.0")
    discount_percentage = Decimal("10")
    product = factories.create_product("p1", shop=shop, supplier=supplier, default_price=default_price)
    product2 = factories.create_product("p2", shop=shop, supplier=supplier, default_price=default_price)

    ProductCatalog.index_product(product)
    ProductCatalog.index_product(product2)
    view = DiscountEditView.as_view()

    # create a 10% discount for the product
    payload = _get_default_discount_data({"product": product.pk, "discount_percentage": str(discount_percentage)})
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=None)
    assert response.status_code == 302

    anon_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    customer_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, contact=contact))

    # discount is indexed
    discounted_price = (default_price - (default_price * discount_percentage * Decimal(0.01))).quantize(Decimal("0.01"))
    _assert_products_queryset(
        anon_catalog,
        [
            (product.pk, default_price, discounted_price),
            (product2.pk, default_price, None),
        ],
    )
    _assert_products_queryset(
        customer_catalog,
        [
            (product.pk, default_price, discounted_price),
            (product2.pk, default_price, None),
        ],
    )

    # changed the discount product
    discount = Discount.objects.last()
    payload = _get_default_discount_data({"product": product2.pk, "discount_percentage": str(discount_percentage)})
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=discount.pk)
    assert response.status_code == 302

    _assert_products_queryset(
        anon_catalog,
        [
            (product.pk, default_price, None),
            (product2.pk, default_price, discounted_price),
        ],
    )
    _assert_products_queryset(
        customer_catalog,
        [
            (product.pk, default_price, None),
            (product2.pk, default_price, discounted_price),
        ],
    )


def test_admin_catalog_discount_category_filter(rf, admin_user):
    shop, supplier, contact, group, category = _init_test()
    default_price = Decimal("15.0")
    discount_amount = Decimal("5")
    product = factories.create_product("p1", shop=shop, supplier=supplier, default_price=default_price)
    product.get_shop_instance(shop).categories.add(category)

    ProductCatalog.index_product(product)
    view = DiscountEditView.as_view()

    # create a $5 discount for the category
    payload = _get_default_discount_data({"category": category.pk, "discount_amount_value": str(discount_amount)})
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=None)
    assert response.status_code == 302

    anon_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    customer_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, contact=contact))

    # discount is indexed
    discounted_price = (default_price - discount_amount).quantize(Decimal("0.01"))
    _assert_products_queryset(anon_catalog, [(product.pk, default_price, discounted_price)])
    _assert_products_queryset(customer_catalog, [(product.pk, default_price, discounted_price)])

    # make the exclude_selected_category flag be True
    discount = Discount.objects.last()
    payload = _get_default_discount_data(
        {
            "category": category.pk,
            "exclude_selected_category": "on",
            "discount_amount_value": str(discount_amount),
        }
    )
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=discount.pk)
    assert response.status_code == 302

    # discounts removed from the product
    _assert_products_queryset(anon_catalog, [(product.pk, default_price, None)])
    _assert_products_queryset(customer_catalog, [(product.pk, default_price, None)])


def test_admin_catalog_discount_contact_group_filter(rf, admin_user):
    shop, supplier, contact, group, category = _init_test()
    default_price = Decimal("15.0")
    discounted_price_value = Decimal("12")
    product = factories.create_product("p1", shop=shop, supplier=supplier, default_price=default_price)
    product.get_shop_instance(shop).categories.add(category)

    ProductCatalog.index_product(product)
    view = DiscountEditView.as_view()

    # create a discounted price for the contact group
    payload = _get_default_discount_data(
        {"contact_group": group.pk, "discounted_price_value": str(discounted_price_value)}
    )
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=None)
    assert response.status_code == 302

    anon_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    customer_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, contact=contact))

    _assert_products_queryset(anon_catalog, [(product.pk, default_price, None)])
    _assert_products_queryset(customer_catalog, [(product.pk, default_price, discounted_price_value)])

    # remove the group from the discount
    discount = Discount.objects.last()
    payload = _get_default_discount_data({"discounted_price_value": str(discounted_price_value)})
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=discount.pk)
    assert response.status_code == 302

    _assert_products_queryset(anon_catalog, [(product.pk, default_price, discounted_price_value)])
    _assert_products_queryset(customer_catalog, [(product.pk, default_price, discounted_price_value)])


def test_admin_catalog_discount_happy_hour_filter(rf, admin_user):
    shop, supplier, contact, group, category = _init_test()
    default_price = Decimal("15.0")
    discounted_price_value = Decimal("12")
    product = factories.create_product("p1", shop=shop, supplier=supplier, default_price=default_price)
    product.get_shop_instance(shop).categories.add(category)

    ProductCatalog.index_product(product)
    discount_view = DiscountEditView.as_view()
    happy_hour_view = HappyHourEditView.as_view()

    # create a happy hour, from 9am to 11am
    payload = {"name": "Mondays", "from_hour": "09:00", "to_hour": "11:00", "weekdays": "0"}
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = happy_hour_view(request, pk=None)
    assert response.status_code == 302

    happy_hour = HappyHour.objects.last()

    # create a discounted price using the happy hour
    payload = _get_default_discount_data(
        {
            "start_datetime": datetime(2021, 1, 1).strftime("%Y-%m-%d %H:%M"),
            "end_datetime": datetime(2022, 1, 1).strftime("%Y-%m-%d %H:%M"),
            "happy_hours": happy_hour.pk,
            "discounted_price_value": str(discounted_price_value),
        }
    )
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = discount_view(request, pk=None)
    assert response.status_code == 302

    catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))

    # # Monday, 6am
    # with patch.object(timezone, "now", return_value=datetime(2021, 1, 4, 6, 0, tzinfo=pytz.utc)):
    #     _assert_products_queryset(catalog, [(product.pk, default_price, None)])
    # # Monday, 10am
    # with patch.object(timezone, "now", return_value=datetime(2021, 1, 4, 10, 0, tzinfo=pytz.utc)):
    #     _assert_products_queryset(catalog, [(product.pk, default_price, discounted_price_value)])

    # change the happy hour time to Tuesdays, from 3pm to 6pm
    discount = happy_hour.discounts.last()
    assert discount
    payload = {"name": "Tuesdays", "from_hour": "15:00", "to_hour": "18:00", "weekdays": "1", "discounts": discount.pk}
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = happy_hour_view(request, pk=happy_hour.pk)
    assert response.status_code == 302

    # Monday, 10am
    with patch.object(timezone, "now", return_value=datetime(2021, 1, 4, 10, 0, tzinfo=pytz.utc)):
        _assert_products_queryset(catalog, [(product.pk, default_price, None)])
    # Monday, 5pm
    with patch.object(timezone, "now", return_value=datetime(2021, 1, 4, 17, 0, tzinfo=pytz.utc)):
        _assert_products_queryset(catalog, [(product.pk, default_price, None)])
    # Tuesday, 5pm
    with patch.object(timezone, "now", return_value=datetime(2021, 1, 5, 17, 0, tzinfo=pytz.utc)):
        _assert_products_queryset(catalog, [(product.pk, default_price, discounted_price_value)])


def _assert_products_queryset(catalog, expected_prices):
    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert products_qs.count() == len(expected_prices)
    for index, value in enumerate(values):
        assert value == expected_prices[index]
