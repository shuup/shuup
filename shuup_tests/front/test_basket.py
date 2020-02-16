# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import pytest
from django.conf import settings
from django.db.models import Sum
from django.utils.translation import activate

from shuup.core.models import ShippingMode
from shuup.default_tax.models import TaxRule
from shuup.front.basket import get_basket
from shuup.front.models import StoredBasket
from shuup.testing.factories import (
    create_default_tax_rule, create_product, get_default_payment_method,
    get_default_shipping_method, get_default_shop, get_default_supplier,
    get_default_tax, get_default_tax_class, get_shipping_method, get_tax
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.money import Money
from shuup.utils.numbers import bankers_round
from shuup_tests.utils import printable_gibberish

from .utils import get_unstocked_package_product_and_stocked_child


@pytest.mark.django_db
def test_basket(rf):
    StoredBasket.objects.all().delete()
    quantities = [3, 12, 44, 23, 65]
    shop = get_default_shop()
    get_default_payment_method()  # Can't create baskets without payment methods
    supplier = get_default_supplier()
    products_and_quantities = []
    for quantity in quantities:
        product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
        products_and_quantities.append((product, quantity))

    for product, q in products_and_quantities:
        request = rf.get("/")
        request.session = {}
        request.shop = shop
        apply_request_middleware(request)
        basket = get_basket(request)
        assert basket == request.basket
        assert basket.product_count == 0
        line = basket.add_product(supplier=supplier, shop=shop, product=product, quantity=q)
        basket.shipping_method = get_shipping_method(shop=shop)  # For shippable product
        assert line.quantity == q
        assert basket.get_lines()
        assert basket.get_product_ids_and_quantities().get(product.pk) == q
        assert basket.product_count == q
        basket.save()
        delattr(request, "basket")
        basket = get_basket(request)
        assert basket.get_product_ids_and_quantities().get(product.pk) == q

        product_ids = set(StoredBasket.objects.last().products.values_list("id", flat=True))
        assert product_ids == set([product.pk])

    stats = StoredBasket.objects.all().aggregate(
        n=Sum("product_count"),
        tfs=Sum("taxful_total_price_value"),
        tls=Sum("taxless_total_price_value"),
    )
    assert stats["n"] == sum(quantities)
    if shop.prices_include_tax:
        assert stats["tfs"] == sum(quantities) * 50
    else:
        assert stats["tls"] == sum(quantities) * 50
    basket.finalize()


@pytest.mark.django_db
def test_basket_dirtying_with_fnl(rf):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    request = rf.get("/")
    request.session = {}
    request.shop = shop
    apply_request_middleware(request)
    basket = get_basket(request)
    line = basket.add_product(
        supplier=supplier,
        shop=shop,
        product=product,
        quantity=1,
        force_new_line=True,
        extra={"foo": "foo"}
    )
    assert basket.dirty  # The change should have dirtied the basket


@pytest.mark.django_db
def test_basket_shipping_error(rf):
    StoredBasket.objects.all().delete()
    shop = get_default_shop()
    supplier = get_default_supplier()
    shipped_product = create_product(
        printable_gibberish(), shop=shop, supplier=supplier, default_price=50,
        shipping_mode=ShippingMode.SHIPPED
    )
    unshipped_product = create_product(
        printable_gibberish(), shop=shop, supplier=supplier, default_price=50,
        shipping_mode=ShippingMode.NOT_SHIPPED
    )

    request = rf.get("/")
    request.session = {}
    request.shop = shop
    apply_request_middleware(request)
    basket = get_basket(request)

    # With a shipped product but no shipping methods, we oughta get an error
    basket.add_product(supplier=supplier, shop=shop, product=shipped_product, quantity=1)
    assert any(ve.code == "no_common_shipping" for ve in basket.get_validation_errors())
    basket.clear_all()

    # But with an unshipped product, we should not
    basket.add_product(supplier=supplier, shop=shop, product=unshipped_product, quantity=1)
    assert not any(ve.code == "no_common_shipping" for ve in basket.get_validation_errors())


@pytest.mark.django_db
def test_basket_data_fields(rf):
    StoredBasket.objects.all().delete()
    shop = get_default_shop()
    request = rf.get("/")
    request.session = {}
    request.shop = shop
    apply_request_middleware(request)
    basket = get_basket(request)
    basket.shipping_data = {"shipment": True}
    basket.payment_data = {"payment": True}
    basket.extra_data = {"extra": True}
    basket.save()
    request.basket = None
    request.baskets = None
    basket = get_basket(request)
    assert basket.shipping_data["shipment"] is True
    assert basket.payment_data["payment"] is True
    assert basket.extra_data["extra"] is True


@pytest.mark.django_db
def test_basket_orderability_change(rf):
    StoredBasket.objects.all().delete()
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    request = rf.get("/")
    request.session = {}
    request.shop = shop
    apply_request_middleware(request)
    basket = get_basket(request)
    line = basket.add_product(
        supplier=supplier,
        shop=shop,
        product=product,
        quantity=1,
        force_new_line=True,
        extra={"foo": "foo"}
    )
    assert len(basket.get_lines()) == 1
    assert len(basket.get_unorderable_lines()) == 0
    product.soft_delete()
    basket.uncache()
    assert basket.dirty
    assert len(basket.get_lines()) == 0
    assert len(basket.get_unorderable_lines()) == 1


@pytest.mark.django_db
def test_basket_orderability_change_shop_product(rf):
    StoredBasket.objects.all().delete()
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    request = rf.get("/")
    request.session = {}
    request.shop = shop
    apply_request_middleware(request)
    basket = get_basket(request)
    line = basket.add_product(
        supplier=supplier,
        shop=shop,
        product=product,
        quantity=1,
        force_new_line=True,
        extra={"foo": "foo"}
    )
    assert len(basket.get_lines()) == 1
    assert len(basket.get_unorderable_lines()) == 0
    product.get_shop_instance(shop).delete()
    basket.uncache()
    assert basket.dirty
    assert len(basket.get_lines()) == 0
    assert len(basket.get_unorderable_lines()) == 1


@pytest.mark.django_db
def test_basket_package_product_orderability_change(rf):
    if "shuup.simple_supplier" not in settings.INSTALLED_APPS:
        pytest.skip("Need shuup.simple_supplier in INSTALLED_APPS")
    from shuup_tests.simple_supplier.utils import get_simple_supplier

    StoredBasket.objects.all().delete()
    shop = get_default_shop()
    supplier = get_simple_supplier()
    product, child = get_unstocked_package_product_and_stocked_child(shop, supplier, child_logical_quantity=2)
    request = rf.get("/")
    request.session = {}
    request.shop = shop
    apply_request_middleware(request)
    basket = get_basket(request)

    # Add the package parent
    basket.add_product(
        supplier=supplier,
        shop=shop,
        product=product,
        quantity=1,
        force_new_line=True,
        extra={"foo": "foo"}
    )

    # Also add the child product separately
    basket.add_product(
        supplier=supplier,
        shop=shop,
        product=child,
        quantity=1,
        force_new_line=True,
        extra={"foo": "foo"}
    )

    # Should be stock for both
    assert len(basket.get_lines()) == 2
    assert len(basket.get_unorderable_lines()) == 0

    supplier.adjust_stock(child.id, -1)

    # Orderability is already cached, we need to uncache to force recheck
    basket.uncache()

    # After reducing stock to 1, should only be stock for one
    assert len(basket.get_lines()) == 1
    assert len(basket.get_unorderable_lines()) == 1

    supplier.adjust_stock(child.id, -1)

    basket.uncache()

    # After reducing stock to 0, should be stock for neither
    assert len(basket.get_lines()) == 0
    assert len(basket.get_unorderable_lines()) == 2


@pytest.mark.django_db
def test_basket_clearing(rf):
    StoredBasket.objects.all().delete()
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    request = rf.get("/")
    request.session = {}
    request.shop = shop
    apply_request_middleware(request)
    basket = get_basket(request)

    pm = get_default_payment_method()
    sm = get_default_shipping_method()
    basket.shipping_method = sm
    basket.payment_method = pm
    basket.save()

    assert basket.shipping_method
    assert basket.payment_method

    basket.clear_all()

    assert not basket.shipping_method
    assert not basket.payment_method
