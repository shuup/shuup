# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.utils import translation

from shuup.core.models import (
    CustomCarrier,
    FixedCostBehaviorComponent,
    OrderLineType,
    PaymentMethod,
    PaymentStatus,
    ShippingMethod,
    WaivingCostBehaviorComponent,
    WeightLimitsBehaviorComponent,
    get_person_contact,
)
from shuup.testing.factories import (
    create_empty_order,
    create_order_with_product,
    create_product,
    get_address,
    get_custom_payment_processor,
    get_default_product,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
    get_payment_method,
    get_payment_processor_with_checkout_phase,
    get_shipping_method,
)
from shuup.testing.models import ExpensiveSwedenBehaviorComponent
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


def get_expensive_sweden_shipping_method():
    carrier = CustomCarrier.objects.create(name="Sveede Sheep")
    sm = carrier.create_service(
        None,
        shop=get_default_shop(),
        enabled=True,
        tax_class=get_default_tax_class(),
        name="Expenseefe-a Svedee Sheepping",
    )
    sm.behavior_components.add(
        ExpensiveSwedenBehaviorComponent.objects.create(),
        WeightLimitsBehaviorComponent.objects.create(min_weight="0.11", max_weight="3"),
    )
    return sm


@pytest.mark.django_db
@pytest.mark.parametrize("country", ["FI", "SE", "NL", "NO"])
def test_methods(admin_user, country):
    contact = get_person_contact(admin_user)
    source = BasketishOrderSource(get_default_shop())
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
        weight=Decimal("0.2"),
    )
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge", country=country)
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = contact

    source.shipping_method = get_expensive_sweden_shipping_method()
    source.payment_method = get_payment_method(name="neat", price=4)
    assert source.shipping_method_id
    assert source.payment_method_id

    errors = list(source.get_validation_errors())

    if country == "FI":
        # "Expenseefe-a Svedee Sheepping" will not allow shipping to
        # Finland, let's see if that holds true
        assert any([ve.code == "we_no_speak_finnish" for ve in errors])
        assert [x.code for x in errors] == ["we_no_speak_finnish"]
        return  # Shouldn't try the rest if we got an error here
    else:
        assert not errors

    final_lines = list(source.get_final_lines())

    assert any(line.type == OrderLineType.SHIPPING for line in final_lines)

    for line in final_lines:
        if line.type == OrderLineType.SHIPPING:
            if country == "SE":  # We _are_ using Expenseefe-a Svedee Sheepping after all.
                assert line.price == source.create_price("5.00")
            else:
                assert line.price == source.create_price("4.00")
            assert line.text == u"Expenseefe-a Svedee Sheepping"
        if line.type == OrderLineType.PAYMENT:
            assert line.price == source.create_price(4)


@pytest.mark.django_db
def test_waiver():
    sm = get_shipping_method(name="Waivey", price=100, waive_at=370)
    source = BasketishOrderSource(get_default_shop())
    assert sm.get_effective_name(source) == u"Waivey"
    assert sm.get_total_cost(source).price == source.create_price(100)
    source.add_line(
        type=OrderLineType.PRODUCT, product=get_default_product(), base_unit_price=source.create_price(400), quantity=1
    )
    assert sm.get_total_cost(source).price == source.create_price(0)


@pytest.mark.django_db
def test_fixed_cost_with_waiving_costs():
    sm = get_shipping_method(name="Fixed and waiving", price=5)

    sm.behavior_components.add(
        *[
            WaivingCostBehaviorComponent.objects.create(price_value=p, waive_limit_value=w)
            for (p, w) in [(3, 5), (7, 10), (10, 30)]
        ]
    )

    source = BasketishOrderSource(get_default_shop())
    source.shipping_method = sm

    def pricestr(pi):
        assert pi.price.unit_matches_with(source.create_price(0))
        return "%.0f EUR (%.0f EUR)" % (pi.price.value, pi.base_price.value)

    assert pricestr(sm.get_total_cost(source)) == "25 EUR (25 EUR)"
    assert source.total_price.value == 25

    source.add_line(
        type=OrderLineType.PRODUCT, product=get_default_product(), base_unit_price=source.create_price(2), quantity=1
    )
    assert pricestr(sm.get_total_cost(source)) == "25 EUR (25 EUR)"
    assert source.total_price.value == 27

    source.add_line(
        type=OrderLineType.PRODUCT, product=get_default_product(), base_unit_price=source.create_price(3), quantity=1
    )
    assert pricestr(sm.get_total_cost(source)) == "22 EUR (25 EUR)"
    assert source.total_price.value == 27

    source.add_line(
        type=OrderLineType.PRODUCT, product=get_default_product(), base_unit_price=source.create_price(10), quantity=1
    )
    assert pricestr(sm.get_total_cost(source)) == "15 EUR (25 EUR)"
    assert source.total_price.value == 30

    source.add_line(
        type=OrderLineType.PRODUCT, product=get_default_product(), base_unit_price=source.create_price(10), quantity=1
    )
    assert pricestr(sm.get_total_cost(source)) == "15 EUR (25 EUR)"
    assert source.total_price.value == 40

    source.add_line(
        type=OrderLineType.PRODUCT, product=get_default_product(), base_unit_price=source.create_price(10), quantity=1
    )
    assert pricestr(sm.get_total_cost(source)) == "5 EUR (25 EUR)"
    assert source.total_price.value == 40


@pytest.mark.django_db
def test_translations_of_method_and_component():
    sm = get_shipping_method(name="Unique shipping")
    sm.set_current_language("en")
    sm.name = "Shipping"
    sm.set_current_language("fi")
    sm.name = "Toimitus"
    sm.save()

    cost = FixedCostBehaviorComponent.objects.language("fi").create(price_value=10, description="kymppi")
    cost.set_current_language("en")
    cost.description = "ten bucks"
    cost.save()
    sm.behavior_components.add(cost)

    source = BasketishOrderSource(get_default_shop())
    source.shipping_method = sm

    translation.activate("fi")
    shipping_lines = [line for line in source.get_final_lines() if line.type == OrderLineType.SHIPPING]
    assert len(shipping_lines) == 1
    assert shipping_lines[0].text == "Toimitus: kymppi"

    translation.activate("en")
    source.uncache()
    shipping_lines = [line for line in source.get_final_lines() if line.type == OrderLineType.SHIPPING]
    assert len(shipping_lines) == 1
    assert shipping_lines[0].text == "Shipping: ten bucks"


@pytest.mark.django_db
def test_weight_limits():
    carrier = CustomCarrier.objects.create()
    sm = carrier.create_service(None, shop=get_default_shop(), enabled=True, tax_class=get_default_tax_class())
    sm.behavior_components.add(WeightLimitsBehaviorComponent.objects.create(min_weight=100, max_weight=500))
    source = BasketishOrderSource(get_default_shop())
    assert any(ve.code == "min_weight" for ve in sm.get_unavailability_reasons(source))
    source.add_line(type=OrderLineType.PRODUCT, weight=600)
    assert any(ve.code == "max_weight" for ve in sm.get_unavailability_reasons(source))


@pytest.mark.django_db
def test_limited_methods():
    """
    Test that products can declare that they limit available shipping methods.
    """
    unique_shipping_method = get_shipping_method(name="unique", price=0)
    shop = get_default_shop()
    common_product = create_product(sku="SH_COMMON", shop=shop)  # A product that does not limit shipping methods
    unique_product = create_product(sku="SH_UNIQUE", shop=shop)  # A product that only supports unique_shipping_method
    unique_shop_product = unique_product.get_shop_instance(shop)
    unique_shop_product.limit_shipping_methods = True
    unique_shop_product.shipping_methods.add(unique_shipping_method)
    unique_shop_product.save()
    impossible_product = create_product(sku="SH_IMP", shop=shop)  # A product that can't be shipped at all
    imp_shop_product = impossible_product.get_shop_instance(shop)
    imp_shop_product.limit_shipping_methods = True
    imp_shop_product.save()
    for product_ids, method_ids in [
        ((common_product.pk, unique_product.pk), (unique_shipping_method.pk,)),
        ((common_product.pk,), ShippingMethod.objects.values_list("pk", flat=True)),
        ((unique_product.pk,), (unique_shipping_method.pk,)),
        (
            (
                unique_product.pk,
                impossible_product.pk,
            ),
            (),
        ),
        (
            (
                common_product.pk,
                impossible_product.pk,
            ),
            (),
        ),
    ]:
        product_ids = set(product_ids)
        assert ShippingMethod.objects.available_ids(shop=shop, products=product_ids) == set(method_ids)


def get_total_price_value(lines):
    return sum([line.price.value for line in lines])


@pytest.mark.django_db
def test_source_lines_with_multiple_fixed_costs():
    """
    Costs with description creates new line always and costs without
    description is combined into one line.
    """
    translation.activate("en")
    starting_price_value = 5
    sm = get_shipping_method(name="Multiple costs", price=starting_price_value)
    sm.behavior_components.clear()

    source = BasketishOrderSource(get_default_shop())
    source.shipping_method = sm

    lines = list(sm.get_lines(source))
    assert len(lines) == 1
    assert get_total_price_value(lines) == Decimal("0")

    sm.behavior_components.add(FixedCostBehaviorComponent.objects.create(price_value=10))
    lines = list(sm.get_lines(source))
    assert len(lines) == 1
    assert get_total_price_value(lines) == Decimal("10")

    sm.behavior_components.add(FixedCostBehaviorComponent.objects.create(price_value=15, description="extra"))
    lines = list(sm.get_lines(source))
    assert len(lines) == 2
    assert get_total_price_value(lines) == Decimal("25")

    sm.behavior_components.add(FixedCostBehaviorComponent.objects.create(price_value=1))
    lines = list(sm.get_lines(source))
    assert len(lines) == 2
    assert get_total_price_value(lines) == Decimal("26")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_payment_processor, expected_final_payment_status",
    [
        (get_custom_payment_processor, PaymentStatus.NOT_PAID),
        (get_payment_processor_with_checkout_phase, PaymentStatus.DEFERRED),
    ],
)
def test_process_payment_return_request(rf, get_payment_processor, expected_final_payment_status):
    """
    Order payment with default payment method with ``CustomPaymentProcessor``
    provider should remain NOT_PAID.

    Order payment with default payment method with ``PaymentWithCheckoutPhase``
    provider should become DEFERRED.

    Payment can't be processed if method doesn't have provider or provider
    is not enabled or payment method is not enabled.
    """
    payment_processor = get_payment_processor()
    pm = PaymentMethod.objects.create(
        shop=get_default_shop(), name="Test method", enabled=False, tax_class=get_default_tax_class()
    )
    product = create_product(sku="test-sku", shop=get_default_shop(), default_price=100)
    order = create_order_with_product(
        product=product,
        supplier=get_default_supplier(),
        quantity=1,
        taxless_base_unit_price=Decimal("5.55"),
        shop=get_default_shop(),
    )
    order.payment_method = pm
    order.save()
    assert order.payment_status == PaymentStatus.NOT_PAID
    with pytest.raises(ValueError):  # Can't process payment with unusable method
        order.payment_method.process_payment_return_request(order, rf.get("/"))
    assert order.payment_status == PaymentStatus.NOT_PAID
    pm.payment_processor = payment_processor
    pm.payment_processor.enabled = False
    pm.save()

    with pytest.raises(ValueError):  # Can't process payment with unusable method
        order.payment_method.process_payment_return_request(order, rf.get("/"))
    assert order.payment_status == PaymentStatus.NOT_PAID
    pm.payment_processor.enabled = True
    pm.save()

    with pytest.raises(ValueError):  # Can't process payment with unusable method
        order.payment_method.process_payment_return_request(order, rf.get("/"))
    assert order.payment_status == PaymentStatus.NOT_PAID
    pm.enabled = True
    pm.save()

    # Add payment data for checkout phase
    order.payment_data = {"input_value": True}
    order.payment_method.process_payment_return_request(order, rf.get("/"))
    assert order.payment_status == expected_final_payment_status


@pytest.mark.django_db
def test_service_methods_with_long_name(rf):
    """
    Make sure that service methods with long names (up to the max length of
    shipping or payment method names) don't cause exceptions when creating
    an order.
    """
    MAX_LENGTH = 100
    long_name = "X" * MAX_LENGTH
    assert len(long_name) == MAX_LENGTH
    sm = ShippingMethod.objects.language("en").create(
        shop=get_default_shop(), name=long_name, enabled=True, tax_class=get_default_tax_class()
    )
    pm = PaymentMethod.objects.language("en").create(
        shop=get_default_shop(), name=long_name, enabled=True, tax_class=get_default_tax_class()
    )
    order = create_empty_order()
    order.shipping_method = sm
    order.payment_method = pm
    order.full_clean()
    order.save()
