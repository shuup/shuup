# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest
import random
from django.test import override_settings
from time import time

from shuup.admin.modules.products.views.edit import ProductEditView
from shuup.core import cache
from shuup.core.catalog import ProductCatalog, ProductCatalogContext
from shuup.core.models import OrderLineType, ShippingMode
from shuup.core.order_creator import OrderCreator, OrderSource
from shuup.simple_supplier.admin_module.forms import SimpleSupplierForm
from shuup.simple_supplier.admin_module.views import (
    process_alert_limit,
    process_stock_adjustment,
    process_stock_managed,
)
from shuup.simple_supplier.models import StockAdjustment, StockCount
from shuup.simple_supplier.notify_events import AlertLimitReached
from shuup.testing.factories import (
    create_order_with_product,
    create_product,
    get_default_shop,
    get_initial_order_status,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
def test_simple_supplier(rf):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop)
    ss = supplier.get_stock_status(product.pk)
    assert ss.logical_count == 0
    num = random.randint(100, 500)
    supplier.adjust_stock(product.pk, +num)
    assert supplier.get_stock_status(product.pk).logical_count == num
    # Create order ...
    order = create_order_with_product(product, supplier, 10, 3, shop=shop)
    quantities = order.get_product_ids_and_quantities()
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == (num - quantities[product.pk])
    assert pss.physical_count == num
    # Create shipment ...
    shipment = order.create_shipment_of_all_products(supplier)
    pss = supplier.get_stock_status(product.pk)
    assert pss.physical_count == (num - quantities[product.pk])
    # Cancel order...
    order.set_canceled()
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == (num)
    # physical stock still the same until shipment exists
    assert pss.physical_count == (num - quantities[product.pk])

    shipment.soft_delete()
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == num
    assert pss.physical_count == num


@pytest.mark.django_db
@pytest.mark.parametrize("stock_managed", [True, False])
def test_supplier_with_stock_counts(rf, stock_managed):
    supplier = get_simple_supplier(stock_managed=stock_managed)
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    quantity = random.randint(100, 600)

    if stock_managed:
        # Adjust
        supplier.adjust_stock(product.pk, quantity)
        # Check that count is adjusted
        assert supplier.get_stock_statuses([product.id])[product.id].logical_count == quantity
        # Since product is stocked with quantity we get no orderability error with quantity
        assert not list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity, customer=None))
        # Since product is stocked with quantity we get orderability error with quantity + 1
        assert list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity + 1, customer=None))
    else:
        # Check that count is not adjusted
        assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 0
        # No orderability errors since product is not stocked
        assert not list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity, customer=None))
        # Turn it to stocked
        supplier.stock_managed = True
        supplier.save()
        supplier.adjust_stock(product.pk, quantity)
        # Check that count is adjusted
        assert supplier.get_stock_statuses([product.id])[product.id].logical_count == quantity
        # No orderability errors since product is stocked with quantity
        assert not list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity, customer=None))
        # Since product is stocked with quantity we get orderability errors with quantity + 1
        assert list(supplier.get_orderability_errors(product.get_shop_instance(shop), quantity + 1, customer=None))


@pytest.mark.django_db
def test_supplier_with_stock_counts_2(rf, admin_user, settings):
    with override_settings(SHUUP_HOME_CURRENCY="USD", SHUUP_ENABLE_MULTIPLE_SHOPS=False):
        supplier = get_simple_supplier()
        shop = get_default_shop()
        assert shop.prices_include_tax
        assert shop.currency != settings.SHUUP_HOME_CURRENCY
        product = create_product("simple-test-product", shop, supplier)
        quantity = random.randint(100, 600)
        supplier.adjust_stock(product.pk, quantity)
        adjust_quantity = random.randint(100, 600)
        request = apply_request_middleware(rf.get("/"), user=admin_user)
        request.POST = {"purchase_price": decimal.Decimal(32.00), "delta": adjust_quantity}
        response = process_stock_adjustment(request, supplier.id, product.id)
        assert response.status_code == 405  # Only POST is allowed
        request.method = "POST"
        response = process_stock_adjustment(request, supplier.id, product.id)
        assert response.status_code == 200
        pss = supplier.get_stock_status(product.pk)
        # Product stock values should be adjusted
        assert pss.logical_count == (quantity + adjust_quantity)
        # test price properties
        sa = StockAdjustment.objects.first()
        assert sa.purchase_price.currency == shop.currency
        assert sa.purchase_price.includes_tax
        sc = StockCount.objects.first()
        assert sc.stock_value.currency == shop.currency
        assert sc.stock_value.includes_tax
        assert sc.stock_unit_price.currency == shop.currency
        assert sc.stock_unit_price.includes_tax

        with override_settings(SHUUP_ENABLE_MULTIPLE_SHOPS=True):
            sa = StockAdjustment.objects.first()  # refetch to invalidate cache
            assert sa.purchase_price.currency != shop.currency
            assert sa.purchase_price.currency == settings.SHUUP_HOME_CURRENCY
            assert not sa.purchase_price.includes_tax
            sc = StockCount.objects.first()
            assert sc.stock_value.currency == settings.SHUUP_HOME_CURRENCY
            assert not sc.stock_value.includes_tax
            assert sc.stock_unit_price.currency == settings.SHUUP_HOME_CURRENCY
            assert not sc.stock_unit_price.includes_tax


@pytest.mark.django_db
def test_admin_form(rf, admin_user):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    frm = SimpleSupplierForm(product=product, request=request)
    # Form contains 1 product even if the product is not stocked
    assert len(frm.products) == 1

    # Now since product is stocked it should be in the form
    frm = SimpleSupplierForm(product=product, request=request)
    assert len(frm.products) == 1

    # Add stocked children for product
    child_product = create_product("child-test-product", shop, supplier)
    child_product.link_to_parent(product)

    # Admin form should now contain only child products for product
    frm = SimpleSupplierForm(product=product, request=request)
    assert len(frm.products) == 1
    assert frm.products[0] == child_product


@pytest.mark.django_db
def test_new_product_admin_form_renders(rf, client, admin_user):
    """
    Make sure that no exceptions are raised when creating a new product
    with simple supplier enabled
    """
    get_default_shop()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view = ProductEditView.as_view()
    supplier = get_simple_supplier()
    supplier.stock_managed = True
    supplier.save()

    # This should not raise an exception
    view(request).render()

    supplier.stock_managed = False
    supplier.save()

    # Nor should this
    view(request).render()


def test_alert_limit_view(rf, admin_user):
    supplier = get_simple_supplier()
    shop = get_default_shop()
    product = create_product("simple-test-product", shop, supplier)
    supplier.update_stock(product.pk)
    sc = StockCount.objects.get(supplier=supplier, product=product)
    assert not sc.alert_limit

    test_alert_limit = decimal.Decimal(10)
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    request.method = "POST"
    request.POST = {
        "alert_limit": test_alert_limit,
    }
    response = process_alert_limit(request, supplier.id, product.id)
    assert response.status_code == 200

    sc = StockCount.objects.get(supplier=supplier, product=product)
    assert sc.alert_limit == test_alert_limit


def test_alert_limit_notification(rf, admin_user):
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_cache",
            }
        }
    ):
        cache.init_cache()

        supplier = get_simple_supplier()
        shop = get_default_shop()
        product = create_product("simple-test-product", shop, supplier)
        supplier.update_stock(product.pk)
        sc = StockCount.objects.get(supplier=supplier, product=product)
        sc.alert_limit = 10
        sc.save()

        # nothing in cache
        cache_key = AlertLimitReached.cache_key_fmt % (supplier.pk, product.pk)
        assert cache.get(cache_key) is None

        # put 11 units in stock
        supplier.adjust_stock(product.pk, +11)

        # still nothing in cache
        cache_key = AlertLimitReached.cache_key_fmt % (supplier.pk, product.pk)
        assert cache.get(cache_key) is None

        event = AlertLimitReached(product=product, supplier=supplier)
        assert event.variable_values["dispatched_last_24hs"] is False

        # stock should be 6, lower then the alert limit
        supplier.adjust_stock(product.pk, -5)
        last_run = cache.get(cache_key)
        assert last_run is not None

        event = AlertLimitReached(product=product, supplier=supplier)
        assert event.variable_values["dispatched_last_24hs"] is True

        # stock should be 1, lower then the alert limit
        supplier.adjust_stock(product.pk, -5)

        # test whether that runs inside a minute
        event = AlertLimitReached(product=product, supplier=supplier)
        event.run(shop)
        # not updated, not ran
        assert cache.get(cache_key) == last_run

        last_run -= 1000
        cache.set(cache_key, last_run)
        event = AlertLimitReached(product=product, supplier=supplier)
        event.run(shop)

        # last run should be updated
        assert cache.get(cache_key) != last_run

        event = AlertLimitReached(
            product=product,
            supplier=supplier,
            supplier_email="supplier-no-break@email.com",
            shop_email="shop-no-break@email.com",
        )
        assert event.variable_values["dispatched_last_24hs"] is True

        # fake we have a cache with more than 24hrs
        cache.set(cache_key, time() - (24 * 60 * 60 * 2))

        event = AlertLimitReached(product=product, supplier=supplier)
        assert event.variable_values["dispatched_last_24hs"] is False


@pytest.mark.django_db
def test_process_stock_managed(rf, admin_user):
    supplier = get_simple_supplier(stock_managed=False)
    shop = get_default_shop()
    product = create_product("simple-test-product", shop)
    request = apply_request_middleware(rf.get("/", data={"stock_managed": True}), user=admin_user)

    response = process_stock_managed(request, supplier.id, product.id)
    assert response.status_code == 405

    request = apply_request_middleware(rf.post("/", data={"stock_managed": True}), user=admin_user)
    response = process_stock_managed(request, supplier.id, product.id)
    assert response.status_code == 200

    # Check no stock count
    sc = StockCount.objects.filter(supplier=supplier, product=product).first()
    assert sc.logical_count == 0
    # Check stock count managed by default
    assert sc.stock_managed is True
    # Now test with stock managed turned off
    request = apply_request_middleware(rf.post("/", data={"stock_managed": False}), user=admin_user)
    response = process_stock_managed(request, supplier.id, product.id)
    assert response.status_code == 200
    # Check stock management is disabled for product
    sc = StockCount.objects.filter(supplier=supplier, product=product).first()
    assert sc.stock_managed is False
    # Now test with stock managed turned on
    request = apply_request_middleware(rf.post("/", data={"stock_managed": True}), user=admin_user)
    response = process_stock_managed(request, supplier.id, product.id)
    assert response.status_code == 200
    # Check stock management is enabled for product
    sc = StockCount.objects.filter(supplier=supplier, product=product).first()
    assert sc.stock_managed is True


@pytest.mark.django_db
@pytest.mark.parametrize("shipping_mode", [ShippingMode.NOT_SHIPPED, ShippingMode.SHIPPED])
def test_supplier_non_shipped_products(rf, shipping_mode):
    """
    Test non shipped products - physical count should have the same as logical count
    """
    supplier = get_simple_supplier(stock_managed=True)
    shop = get_default_shop()
    product = create_product("shipped-product", shop, supplier, shipping_mode=shipping_mode)
    quantity = random.randint(100, 600)

    # Adjust
    supplier.adjust_stock(product.pk, quantity)
    stock_status = supplier.get_stock_status(product.id)

    # Check that count is adjusted
    assert stock_status.logical_count == quantity
    assert stock_status.physical_count == quantity

    # Create order ...
    order = create_order_with_product(product, supplier, 10, 3, shop=shop)
    quantities = order.get_product_ids_and_quantities()
    stock_status = supplier.get_stock_status(product.id)

    assert stock_status.logical_count == (quantity - quantities[product.pk])
    if shipping_mode == ShippingMode.SHIPPED:
        assert stock_status.physical_count == quantity

        # Create shipment ...
        shipment = order.create_shipment_of_all_products(supplier)
        stock_status = supplier.get_stock_status(product.id)
        assert stock_status.physical_count == (quantity - quantities[product.pk])

    else:
        assert stock_status.physical_count == stock_status.logical_count

    # Cancel order...
    order.set_canceled()

    if shipping_mode == ShippingMode.SHIPPED:
        shipment.soft_delete()

    stock_status = supplier.get_stock_status(product.id)
    assert stock_status.logical_count == quantity
    assert stock_status.physical_count == stock_status.logical_count


@pytest.mark.django_db
def test_product_catalog_indexing(rf, admin_user, settings):
    shop = get_default_shop()
    supplier = get_simple_supplier(shop=shop)
    supplier.stock_managed = True
    supplier.save()
    product = create_product("simple-test-product", shop, supplier)

    ProductCatalog.index_product(product)

    # no purchasable products
    catalog = ProductCatalog(ProductCatalogContext(shop=shop, purchasable_only=True))
    assert catalog.get_products_queryset().count() == 0

    # add 10 items to the stock
    stock_qty = 10
    request = apply_request_middleware(
        rf.post("/", data={"purchase_price": decimal.Decimal(32.00), "delta": stock_qty}), user=admin_user
    )
    response = process_stock_adjustment(request, supplier.id, product.id)
    assert response.status_code == 200
    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == stock_qty

    # now there are purchasable products
    assert catalog.get_products_queryset().count() == 1
    assert product in catalog.get_products_queryset()

    # create a random order with 10 units of the product
    source = OrderSource(shop)
    source.status = get_initial_order_status()
    source.add_line(
        type=OrderLineType.PRODUCT,
        supplier=supplier,
        product=product,
        base_unit_price=source.create_price(1),
        quantity=10,
    )
    OrderCreator().create_order(source)

    pss = supplier.get_stock_status(product.pk)
    assert pss.logical_count == 0

    # stocks are gone
    assert catalog.get_products_queryset().count() == 0
