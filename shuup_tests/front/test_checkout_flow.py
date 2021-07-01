# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import random

from shuup.core import cache
from shuup.core.models import Order, PaymentStatus, Product
from shuup.front.signals import checkout_complete
from shuup.testing.factories import (
    create_default_order_statuses,
    create_product,
    get_address,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
)
from shuup.testing.mock_population import populate_if_required
from shuup.testing.models import CarrierWithCheckoutPhase, PaymentWithCheckoutPhase
from shuup.testing.soup_utils import extract_form_fields
from shuup.utils.django_compat import reverse
from shuup_tests.front.utils import checkout_complete_signal
from shuup_tests.utils import SmartClient


def fill_address_inputs(soup, with_company=False):
    inputs = {}
    test_address = get_address()
    for key, value in extract_form_fields(soup.find("form", id="addresses")).items():
        if not value:
            if key in ("order-tax_number", "order-company_name"):
                continue
            if key.startswith("shipping-") or key.startswith("billing-"):
                bit = key.split("-")[1]
                value = getattr(test_address, bit, None)
            if not value and "email" in key:
                value = "test%d@example.shuup.com" % random.random()
            if not value:
                value = "test"
        inputs[key] = value or ""  # prevent None as data

    if with_company:
        inputs["company-tax_number"] = "FI1234567-1"
        inputs["company-company_name"] = "Example Oy"
    else:
        inputs = dict((k, v) for (k, v) in inputs.items() if not k.startswith("company-"))

    return inputs


def _populate_client_basket(client):
    product_ids = []
    index = client.soup("/")
    product_links = index.find_all("a", rel="product-detail")
    assert product_links
    for i in range(3):  # add three different products
        product_detail_path = product_links[i]["href"]
        assert product_detail_path
        product_detail_soup = client.soup(product_detail_path)
        inputs = extract_form_fields(product_detail_soup)
        basket_path = reverse("shuup:basket")
        add_to_basket_resp = client.post(
            basket_path,
            data={
                "command": "add",
                "product_id": inputs["product_id"],
                "quantity": 1,
                "supplier": get_default_supplier().pk,
            },
        )
        assert add_to_basket_resp.status_code < 400
        product_ids.append(inputs["product_id"])
    basket_soup = client.soup(basket_path)
    assert b"no such element" not in basket_soup.renderContents(), "All product details are not rendered correctly"
    return product_ids


def _get_payment_method_with_phase():
    processor = PaymentWithCheckoutPhase.objects.create(identifier="processor_with_phase", enabled=True)
    assert isinstance(processor, PaymentWithCheckoutPhase)
    return processor.create_service(
        None,
        identifier="payment_with_phase",
        shop=get_default_shop(),
        name="Test method with phase",
        enabled=True,
        tax_class=get_default_tax_class(),
    )


def _get_shipping_method_with_phase():
    carrier = CarrierWithCheckoutPhase.objects.create(identifier="carrier_with_phase", enabled=True)
    assert isinstance(carrier, CarrierWithCheckoutPhase)
    return carrier.create_service(
        None,
        identifier="carrier_with_phase",
        shop=get_default_shop(),
        name="Test method with phase",
        enabled=True,
        tax_class=get_default_tax_class(),
    )


@pytest.mark.django_db
@pytest.mark.parametrize("with_company, with_signal", [(False, True), (True, True), (False, False), (True, False)])
def test_basic_order_flow(with_company, with_signal):
    cache.clear()
    create_default_order_statuses()
    n_orders_pre = Order.objects.count()
    populate_if_required()
    c = SmartClient()
    product_ids = _populate_client_basket(c)

    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    addresses_soup = c.soup(addresses_path)
    inputs = fill_address_inputs(addresses_soup, with_company=with_company)
    response = c.post(addresses_path, data=inputs)
    assert response.status_code == 302  # Should redirect forth

    # Make sure the address is initialized from storage
    # Go back to addresses right before back to methods
    c.soup(addresses_path)

    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    methods_soup = c.soup(methods_path)
    assert c.post(methods_path, data=extract_form_fields(methods_soup)).status_code == 302  # Should redirect forth

    if with_signal:
        checkout_complete.connect(checkout_complete_signal, dispatch_uid="checkout_complete_signal")

    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})
    confirm_soup = c.soup(confirm_path)
    Product.objects.get(pk=product_ids[0]).soft_delete()
    assert c.post(confirm_path, data=extract_form_fields(confirm_soup)).status_code == 200  # user needs to reconfirm
    data = extract_form_fields(confirm_soup)
    data["accept_terms"] = True
    data["product_ids"] = ",".join(product_ids[1:])
    assert c.post(confirm_path, data=data).status_code == 302  # Should redirect forth

    n_orders_post = Order.objects.count()
    assert n_orders_post > n_orders_pre, "order was created"

    order = Order.objects.first()
    expected_ip = "127.0.0.2" if with_signal else "127.0.0.1"
    assert order.ip_address == expected_ip

    if with_signal:
        checkout_complete.disconnect(dispatch_uid="checkout_complete_signal")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_shipping_method,shipping_data,get_payment_method,payment_data,cancel_order",
    [
        (get_default_shipping_method, None, _get_payment_method_with_phase, {"input_field": True}, True),
        (get_default_shipping_method, None, _get_payment_method_with_phase, {"input_field": True}, False),
        (_get_shipping_method_with_phase, {"input_field": "20540"}, get_default_payment_method, None, False),
        (
            _get_shipping_method_with_phase,
            {"input_field": "20540"},
            _get_payment_method_with_phase,
            {"input_field": True},
            False,
        ),
    ],
)
def test_order_flow_with_phases(get_shipping_method, shipping_data, get_payment_method, payment_data, cancel_order):
    cache.clear()
    create_default_order_statuses()
    populate_if_required()
    c = SmartClient()
    _populate_client_basket(c)

    # Create methods
    shipping_method = get_shipping_method()
    payment_method = get_payment_method()
    # Resolve paths
    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    shipping_path = reverse("shuup:checkout", kwargs={"phase": "shipping"})
    payment_path = reverse("shuup:checkout", kwargs={"phase": "payment"})
    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})

    # Phase: Addresses
    addresses_soup = c.soup(addresses_path)
    inputs = fill_address_inputs(addresses_soup, with_company=False)
    response = c.post(addresses_path, data=inputs)
    assert response.status_code == 302, "Address phase should redirect forth to methods"

    # Phase: Methods
    response = c.get(methods_path)
    assert response.status_code == 200
    response = c.post(methods_path, data={"shipping_method": shipping_method.pk, "payment_method": payment_method.pk})
    assert response.status_code == 302, "Methods phase should redirect forth"

    if isinstance(shipping_method.carrier, CarrierWithCheckoutPhase):
        # Phase: Shipping
        response = c.get(shipping_path)
        assert response.status_code == 200
        response = c.post(shipping_path, data=shipping_data)
        assert response.status_code == 302, "Payments phase should redirect forth"

    if isinstance(payment_method.payment_processor, PaymentWithCheckoutPhase):
        # Phase: payment
        response = c.get(payment_path)
        assert response.status_code == 200
        response = c.post(payment_path, data=payment_data)
        assert response.status_code == 302, "Payments phase should redirect forth"

    # Phase: Confirm
    assert Order.objects.count() == 0
    confirm_soup = c.soup(confirm_path)

    data = extract_form_fields(confirm_soup)
    data["accept_terms"] = True
    response = c.post(confirm_path, data)
    assert response.status_code == 302, "Confirm should redirect forth"

    order = Order.objects.first()

    if cancel_order:
        order.set_canceled()
        process_payment_path = reverse("shuup:order_process_payment", kwargs={"pk": order.pk, "key": order.key})
        process_payment_return_path = reverse("shuup:order_complete", kwargs={"pk": order.pk, "key": order.key})
        response = c.get(process_payment_path)
        assert response.status_code == 302, "Payment page should redirect back"
        assert response.url.endswith(process_payment_return_path)
        return

    if isinstance(shipping_method.carrier, CarrierWithCheckoutPhase):
        assert order.shipping_data.get("input_value") == "20540"

    if isinstance(payment_method.payment_processor, PaymentWithCheckoutPhase):
        assert order.payment_data.get("input_value")
        assert order.payment_status == PaymentStatus.NOT_PAID
        # Resolve order specific paths (payment and complete)
        process_payment_path = reverse("shuup:order_process_payment", kwargs={"pk": order.pk, "key": order.key})
        process_payment_return_path = reverse(
            "shuup:order_process_payment_return", kwargs={"pk": order.pk, "key": order.key}
        )
        order_complete_path = reverse("shuup:order_complete", kwargs={"pk": order.pk, "key": order.key})

        # Check confirm redirection to payment page
        assert response.url.endswith(process_payment_path), "Confirm should have redirected to payment page"

        # Visit payment page
        response = c.get(process_payment_path)
        assert response.status_code == 302, "Payment page should redirect forth"
        assert response.url.endswith(process_payment_return_path)

        # Check payment return
        response = c.get(process_payment_return_path)
        assert response.status_code == 302, "Payment return should redirect forth"
        assert response.url.endswith(order_complete_path)

        # Check payment status has changed to DEFERRED
        order = Order.objects.get(pk=order.pk)  # reload
        assert order.payment_status == PaymentStatus.DEFERRED


@pytest.mark.django_db
def test_checkout_empty_basket(rf):
    cache.clear()
    create_default_order_statuses()
    n_orders_pre = Order.objects.count()
    populate_if_required()
    c = SmartClient()
    product_ids = _populate_client_basket(c)
    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    addresses_soup = c.soup(addresses_path)
    inputs = fill_address_inputs(addresses_soup)
    for product_id in product_ids:
        Product.objects.get(pk=product_id).soft_delete()
    response, soup = c.response_and_soup(addresses_path, data=inputs, method="post")
    assert response.status_code == 200  # Should redirect forth
    assert b"Your shopping cart is empty." in soup.renderContents()
