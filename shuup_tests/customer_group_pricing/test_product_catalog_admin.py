# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal
from mock import patch

from shuup.admin.modules.products.views.edit import ProductEditView
from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import PersonContact, Product, ProductVisibility, ShippingMode, ShopProductVisibility
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import atomic_commit_mock


def test_admin_custom_customer_price_updates(rf, admin_user):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    contact = factories.create_random_person()
    group = PersonContact.get_default_group()
    contact.groups.add(group)
    product_type = factories.get_default_product_type()
    tax_class = factories.get_default_tax_class()
    sales_unit = factories.get_default_sales_unit()

    view = ProductEditView.as_view()
    group_price = "10.0"
    default_price = "15.0"

    payload = {
        "base-name__en": "My Product",
        "base-type": product_type.pk,
        "base-sku": "p1",
        "base-shipping_mode": ShippingMode.NOT_SHIPPED.value,
        "base-tax_class": tax_class.pk,
        "base-sales_unit": sales_unit.pk,
        "base-width": "0",
        "base-height": "0",
        "base-depth": "0",
        "base-net_weight": "0",
        "base-gross_weight": "0",
        f"shop{shop.pk}-default_price_value": default_price,
        f"shop{shop.pk}-visibility": ShopProductVisibility.ALWAYS_VISIBLE.value,
        f"shop{shop.pk}-visibility_limit": ProductVisibility.VISIBLE_TO_ALL.value,
        f"shop{shop.pk}-minimum_purchase_quantity": "1",
        f"shop{shop.pk}-purchase_multiple": "1",
        f"shop{shop.pk}-suppliers": [supplier.pk],
        f"customer_group_pricing-s_{shop.pk}_g_{group.pk}": group_price,  # set price for the group
    }

    # create a new product
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=None)

    assert response.status_code == 302

    anon_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    customer_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, contact=contact))

    product = Product.objects.first()
    _assert_products_queryset(anon_catalog, [(product.pk, Decimal(default_price), None)])
    _assert_products_queryset(customer_catalog, [(product.pk, Decimal(group_price), None)])

    payload.update(
        {
            # remove the customer group price
            f"customer_group_pricing-s_{shop.pk}_g_{group.pk}": "",
            "media-TOTAL_FORMS": 0,
            "media-INITIAL_FORMS": 0,
            "media-MIN_NUM_FORMS": 0,
            "media-MAX_NUM_FORMS": 1000,
            "images-TOTAL_FORMS": 0,
            "images-INITIAL_FORMS": 0,
            "images-MIN_NUM_FORMS": 0,
            "images-MAX_NUM_FORMS": 1000,
        }
    )

    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=product.get_shop_instance(shop).pk)
    assert response.status_code == 302

    # default price for both
    _assert_products_queryset(anon_catalog, [(product.pk, Decimal(default_price), None)])
    _assert_products_queryset(customer_catalog, [(product.pk, Decimal(default_price), None)])


def test_admin_custom_customer_discount_updates(rf, admin_user):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    contact = factories.create_random_person()
    group = PersonContact.get_default_group()
    contact.groups.add(group)
    product_type = factories.get_default_product_type()
    tax_class = factories.get_default_tax_class()
    sales_unit = factories.get_default_sales_unit()

    view = ProductEditView.as_view()
    discount_amount = "5.0"
    default_price = "15.0"

    payload = {
        "base-name__en": "My Product",
        "base-type": product_type.pk,
        "base-sku": "p1",
        "base-shipping_mode": ShippingMode.NOT_SHIPPED.value,
        "base-tax_class": tax_class.pk,
        "base-sales_unit": sales_unit.pk,
        "base-width": "0",
        "base-height": "0",
        "base-depth": "0",
        "base-net_weight": "0",
        "base-gross_weight": "0",
        f"shop{shop.pk}-default_price_value": default_price,
        f"shop{shop.pk}-visibility": ShopProductVisibility.ALWAYS_VISIBLE.value,
        f"shop{shop.pk}-visibility_limit": ProductVisibility.VISIBLE_TO_ALL.value,
        f"shop{shop.pk}-minimum_purchase_quantity": "1",
        f"shop{shop.pk}-purchase_multiple": "1",
        f"shop{shop.pk}-suppliers": [supplier.pk],
        f"customer_group_discount-s_{shop.pk}_g_{group.pk}": discount_amount,  # set discount amount for the group
    }

    # create a new product
    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=None)

    assert response.status_code == 302

    anon_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False))
    customer_catalog = ProductCatalog(context=ProductCatalogContext(purchasable_only=False, contact=contact))

    product = Product.objects.first()
    _assert_products_queryset(anon_catalog, [(product.pk, Decimal(default_price), None)])
    _assert_products_queryset(customer_catalog, [(product.pk, Decimal(default_price), Decimal("10"))])

    payload.update(
        {
            # remove the customer group discount
            f"customer_group_discount-s_{shop.pk}_g_{group.pk}": "",
            "media-TOTAL_FORMS": 0,
            "media-INITIAL_FORMS": 0,
            "media-MIN_NUM_FORMS": 0,
            "media-MAX_NUM_FORMS": 1000,
            "images-TOTAL_FORMS": 0,
            "images-INITIAL_FORMS": 0,
            "images-MIN_NUM_FORMS": 0,
            "images-MAX_NUM_FORMS": 1000,
        }
    )

    request = apply_request_middleware(rf.post("/", data=payload), shop=shop, user=admin_user)
    with patch("django.db.transaction.on_commit", new=atomic_commit_mock):
        response = view(request, pk=product.get_shop_instance(shop).pk)
    assert response.status_code == 302

    # no discount for both
    _assert_products_queryset(anon_catalog, [(product.pk, Decimal(default_price), None)])
    _assert_products_queryset(customer_catalog, [(product.pk, Decimal(default_price), None)])


def _assert_products_queryset(catalog, expected_prices):
    products_qs = catalog.get_products_queryset().order_by("catalog_price")
    values = products_qs.values_list("pk", "catalog_price", "catalog_discounted_price")
    assert products_qs.count() == len(expected_prices)
    for index, value in enumerate(values):
        assert value == expected_prices[index]
