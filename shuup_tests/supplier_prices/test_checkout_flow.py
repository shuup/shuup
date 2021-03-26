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

from shuup.core import cache
from shuup.core.models import Order, Supplier
from shuup.testing import factories
from shuup.testing.models import SupplierPrice
from shuup.testing.soup_utils import extract_form_fields
from shuup.themes.classic_gray.theme import ClassicGrayTheme
from shuup.utils.django_compat import reverse
from shuup.xtheme.models import ThemeSettings
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_order_flow_with_multiple_suppliers():
    cache.clear()

    shop = factories.get_default_shop()
    factories.create_default_order_statuses()
    factories.get_default_payment_method()
    factories.get_default_shipping_method()

    n_orders_pre = Order.objects.count()
    product = factories.create_product("sku", shop=shop, default_price=30)
    shop_product = product.get_shop_instance(shop)

    # Activate show supplier info for front
    assert ThemeSettings.objects.count() == 1
    theme_settings = ThemeSettings.objects.first()
    theme_settings.update_settings({"show_supplier_info": True})

    supplier_data = [
        ("Johnny Inc", 30),
        ("Mike Inc", 10),
        ("Simon Inc", 20),
    ]
    for name, product_price in supplier_data:
        supplier = Supplier.objects.create(name=name)
        supplier.shops.add(shop_product.shop)
        shop_product.suppliers.add(supplier)
        SupplierPrice.objects.create(supplier=supplier, shop=shop, product=product, amount_value=product_price)

    strategy = "shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy"
    with override_settings(SHUUP_PRICING_MODULE="supplier_pricing", SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY=strategy):

        # Ok so cheapest price should be default supplier
        expected_supplier = shop_product.get_supplier()
        assert expected_supplier.name == "Mike Inc"
        with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
            c = SmartClient()

            # Case 1: use default supplier
            _add_to_basket(c, product.pk, 2)
            order = _complete_checkout(c, n_orders_pre + 1)
            assert order
            product_lines = order.lines.products()
            assert len(product_lines) == 1
            assert product_lines[0].supplier.pk == expected_supplier.pk
            assert product_lines[0].base_unit_price_value == decimal.Decimal("10")

            # Case 2: force supplier to Johnny Inc
            johnny_supplier = Supplier.objects.filter(name="Johnny Inc").first()
            _add_to_basket(c, product.pk, 3, johnny_supplier)
            order = _complete_checkout(c, n_orders_pre + 2)
            assert order
            product_lines = order.lines.products()
            assert len(product_lines) == 1
            assert product_lines[0].supplier.pk == johnny_supplier.pk
            assert product_lines[0].base_unit_price_value == decimal.Decimal("30")

            # Case 3: order 2 pcs from Mike and 3 pcs from Simon Inc
            mike_supplier = Supplier.objects.filter(name="Mike Inc").first()
            _add_to_basket(c, product.pk, 2, mike_supplier)

            simon_supplier = Supplier.objects.filter(name="Simon Inc").first()
            _add_to_basket(c, product.pk, 3, simon_supplier)

            order = _complete_checkout(c, n_orders_pre + 3)
            assert order
            assert order.taxful_total_price_value == decimal.Decimal("80")  # Math: 2x10e + 3x20e

            product_lines = order.lines.products()
            assert len(product_lines) == 2

            mikes_line = [line for line in product_lines if line.supplier.pk == mike_supplier.pk][0]
            assert mikes_line
            assert mikes_line.quantity == 2
            assert mikes_line.base_unit_price_value == decimal.Decimal("10")

            simon_line = [line for line in product_lines if line.supplier.pk == simon_supplier.pk][0]
            assert simon_line
            assert simon_line.quantity == 3
            assert simon_line.base_unit_price_value == decimal.Decimal("20")


def _add_to_basket(client, product_id, quantity, supplier=None):
    data = {"command": "add", "product_id": product_id, "quantity": quantity}
    if supplier:
        data.update({"supplier_id": supplier.id})

    add_to_basket_resp = client.post(reverse("shuup:basket"), data=data)
    assert add_to_basket_resp.status_code < 400


def _complete_checkout(client, expected_order_count):
    addresses_path = reverse("shuup:checkout", kwargs={"phase": "addresses"})
    addresses_soup = client.soup(addresses_path)
    inputs = _fill_address_inputs(addresses_soup, with_company=False)
    response = client.post(addresses_path, data=inputs)
    assert response.status_code == 302  # Should redirect forth

    # Make sure the address is initialized from storage
    # Go back to addresses right before back to methods
    client.soup(addresses_path)

    methods_path = reverse("shuup:checkout", kwargs={"phase": "methods"})
    methods_soup = client.soup(methods_path)
    assert client.post(methods_path, data=extract_form_fields(methods_soup)).status_code == 302  # Should redirect forth

    confirm_path = reverse("shuup:checkout", kwargs={"phase": "confirm"})
    confirm_soup = client.soup(confirm_path)
    data = extract_form_fields(confirm_soup)
    data["accept_terms"] = True
    assert client.post(confirm_path, data=data).status_code == 302  # Should redirect forth

    n_orders_post = Order.objects.count()
    assert n_orders_post == expected_order_count, "order was created"
    return Order.objects.order_by("-id").first()


def _fill_address_inputs(soup, with_company=False):
    inputs = {}
    test_address = factories.get_address()
    for key, value in extract_form_fields(soup.find("form", id="addresses")).items():
        if not value:
            if key in ("order-tax_number", "order-company_name"):
                continue
            if key.startswith("shipping-") or key.startswith("billing-"):
                bit = key.split("-")[1]
                value = getattr(test_address, bit, None)
            if not value and "email" in key:
                value = "test%d@example.com" % random.random()
            if not value:
                value = "test"
        inputs[key] = value

    if with_company:
        inputs["company-tax_number"] = "FI1234567-1"
        inputs["company-company_name"] = "Example Oy"
    else:
        inputs = dict((k, v) for (k, v) in inputs.items() if not k.startswith("company-"))

    return inputs
