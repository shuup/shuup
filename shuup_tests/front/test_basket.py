# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum
from django.utils.translation import activate

from shuup.core.models import ShippingMode
from shuup.default_tax.models import TaxRule
from shuup.front.basket import get_basket
from shuup.front.models import StoredBasket
from shuup.testing.factories import (
    create_default_tax_rule,
    create_product,
    create_random_address,
    create_random_user,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_default_tax,
    get_default_tax_class,
    get_shipping_method,
    get_tax,
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

        # Since ordering the latest basket is first in line
        product_ids = set(StoredBasket.objects.first().products.values_list("id", flat=True))
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
        supplier=supplier, shop=shop, product=product, quantity=1, force_new_line=True, extra={"foo": "foo"}
    )
    assert basket.dirty  # The change should have dirtied the basket


@pytest.mark.django_db
def test_basket_shipping_error(rf):
    StoredBasket.objects.all().delete()
    shop = get_default_shop()
    supplier = get_default_supplier()
    shipped_product = create_product(
        printable_gibberish(), shop=shop, supplier=supplier, default_price=50, shipping_mode=ShippingMode.SHIPPED
    )
    unshipped_product = create_product(
        printable_gibberish(), shop=shop, supplier=supplier, default_price=50, shipping_mode=ShippingMode.NOT_SHIPPED
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
        supplier=supplier, shop=shop, product=product, quantity=1, force_new_line=True, extra={"foo": "foo"}
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
        supplier=supplier, shop=shop, product=product, quantity=1, force_new_line=True, extra={"foo": "foo"}
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
        supplier=supplier, shop=shop, product=product, quantity=1, force_new_line=True, extra={"foo": "foo"}
    )

    # Also add the child product separately
    basket.add_product(
        supplier=supplier, shop=shop, product=child, quantity=1, force_new_line=True, extra={"foo": "foo"}
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


@pytest.mark.django_db
def test_basket_store_addresses(rf):
    """
    Make sure the shipping and billing addresses
    are saved as plain when the address is not
    previously created in the database (existing MutableAddress)
    """
    StoredBasket.objects.all().delete()
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    request = apply_request_middleware(rf.get("/"), shop=shop)
    basket = get_basket(request)
    assert not basket.billing_address
    assert not basket.shipping_address

    shipping_address = create_random_address(save=False)
    billing_address = create_random_address(save=False)

    basket.shipping_address = shipping_address
    basket.billing_address = billing_address
    basket.save()
    basket_key = basket.storage.get_basket_kwargs(basket)["key"]

    # let use the same session later
    session = request.session

    assert basket.shipping_address and basket.shipping_address.name
    assert basket.billing_address and basket.billing_address.name

    # address are not saved model instances
    assert not basket.shipping_address.id
    assert not basket.billing_address.id

    # load the basket, it should load the address data
    request = apply_request_middleware(rf.get("/"), shop=shop)
    request.session = session
    basket = get_basket(request)

    assert basket.shipping_address.as_string_list() == shipping_address.as_string_list()
    assert basket.billing_address.as_string_list() == billing_address.as_string_list()


@pytest.mark.django_db
def test_basket_extra_data(rf):
    shop = get_default_shop()
    user = create_random_user()

    request = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    basket1 = get_basket(request, basket_name="basket")

    basket1.extra_data["my"] = "value"
    basket1.shipping_data["ship"] = "there"
    basket1.payment_data["token"] = "qwerty"

    assert basket1.extra_data["my"] == "value"
    assert basket1.shipping_data["ship"] == "there"
    assert basket1.payment_data["token"] == "qwerty"

    stored_basket = basket1.save()
    loaded_data = basket1.storage.load(basket1)
    assert loaded_data["extra_data"] == basket1.extra_data
    assert loaded_data["payment_data"] == basket1.payment_data
    assert loaded_data["shipping_data"] == basket1.shipping_data

    # make sure the data is clear
    request2 = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    basket2 = get_basket(request2, basket_name="basket2")
    assert not basket2.extra_data
    assert not basket2.shipping_data
    assert not basket2.payment_data

    # make sure the saved basket is loaded from the storage
    request3 = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    request3.session = request.session
    request3.basket = None
    basket3 = get_basket(request3, basket_name="basket")
    assert basket3.extra_data["my"] == basket1.extra_data["my"]
    assert basket3.shipping_data["ship"] == basket1.shipping_data["ship"]
    assert basket3.payment_data["token"] == basket1.payment_data["token"]


@pytest.mark.django_db
def test_bsket_log_entries(rf):
    shop = get_default_shop()
    user = create_random_user()
    request = apply_request_middleware(rf.get("/"), user=user, shop=shop)
    basket = get_basket(request, basket_name="basket")
    basket.add_log_entry("hello")
    assert len(basket.get_log_entries()) == 1

    basket.shop = None  # No shop no log entry
    basket.add_log_entry("hello world")
    assert len(basket.get_log_entries()) == 0  # No shop returns empty list

    basket.shop = shop
    basket.add_log_entry("hello world")
    assert len(basket.get_log_entries()) == 2
