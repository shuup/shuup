# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test.utils import override_settings

from shoop.apps.provides import override_provides
from shoop.core.methods.base import BaseShippingMethodModule
from shoop.core.models import (
    get_person_contact, OrderLineType, PaymentMethod, ShippingMethod
)
from shoop.core.order_creator import SourceLine
from shoop.core.pricing import PriceInfo
from shoop.testing.factories import (
    create_product, get_address, get_default_product, get_default_shop,
    get_default_supplier, get_default_tax_class
)
from shoop_tests.utils.basketish_order_source import BasketishOrderSource


class ExpensiveSwedenShippingModule(BaseShippingMethodModule):
    identifier = "expensive_sweden"
    name = "Expensive Sweden Shipping"

    def get_effective_name(self, source, **kwargs):
        return u"Expenseefe-a Svedee Sheepping"

    def get_effective_price_info(self, source, **kwargs):
        four = source.shop.create_price('4.00')
        five = source.shop.create_price('5.00')
        if source.shipping_address and source.shipping_address.country == "SE":
            return PriceInfo(five, four, 1)
        return PriceInfo(four, four, 1)

    def get_validation_errors(self, source, **kwargs):
        for error in super(ExpensiveSwedenShippingModule, self).get_validation_errors(source, **kwargs):
            # The following line is no cover because the parent class doesn't necessarily error out
            yield error  # pragma: no cover


        if source.shipping_address and source.shipping_address.country == "FI":
            yield ValidationError("Veell nut sheep unytheeng tu Feenlund!", code="we_no_speak_finnish")


SHIPPING_METHOD_SPEC = "%s:%s" % (__name__, ExpensiveSwedenShippingModule.__name__)


def get_expensive_sweden_shipping_method():
    sm = ShippingMethod(
        identifier=ExpensiveSwedenShippingModule.identifier,
        module_identifier=ExpensiveSwedenShippingModule.identifier,
        tax_class=get_default_tax_class()
    )
    sm.module_data = {
        "min_weight": "0.11000000",
        "max_weight": "3.00000000",
        "price_waiver_product_minimum": "370"
    }
    sm.save()
    return sm

def override_provides_for_expensive_sweden_shipping_method():
    return override_provides("shipping_method_module", [SHIPPING_METHOD_SPEC])

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
        weight=Decimal("0.2")
    )
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge", country=country)
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = contact

    with override_provides_for_expensive_sweden_shipping_method():
        source.shipping_method = get_expensive_sweden_shipping_method()
        source.payment_method = PaymentMethod.objects.create(identifier="neat",
                                                             module_data={"price": 4},
                                                             tax_class=get_default_tax_class())
        assert source.shipping_method_id
        assert source.payment_method_id

        errors = list(source.get_validation_errors())

        if country == "FI":  # "Expenseefe-a Svedee Sheepping" will not allow shipping to Finland, let's see if that holds true
            assert any([ve.code == "we_no_speak_finnish" for ve in errors])
            return  # Shouldn't try the rest if we got an error here
        else:
            assert not errors

        final_lines = list(source.get_final_lines())

        assert any(line.type == OrderLineType.SHIPPING for line in final_lines)

        for line in final_lines:
            if line.type == OrderLineType.SHIPPING:
                if country == "SE":  # We _are_ using Expenseefe-a Svedee Sheepping after all.
                    assert line.price == source.shop.create_price("5.00")
                else:
                    assert line.price == source.shop.create_price("4.00")
                assert line.text == u"Expenseefe-a Svedee Sheepping"
            if line.type == OrderLineType.PAYMENT:
                assert line.price == source.shop.create_price(4)


@pytest.mark.django_db
def test_method_list(admin_user):
    with override_provides_for_expensive_sweden_shipping_method():
        assert any(name == "Expensive Sweden Shipping" for (spec, name) in ShippingMethod.get_module_choices())

@pytest.mark.django_db
def test_waiver():
    sm = ShippingMethod(name="Waivey", tax_class=get_default_tax_class(),
                        module_data={
                            "price_waiver_product_minimum": "370",
                            "price": "100"
                        })
    source = BasketishOrderSource(get_default_shop())
    assert sm.get_effective_name(source) == u"Waivey"
    assert sm.get_effective_price_info(source).price == source.shop.create_price(100)
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        base_unit_price=source.shop.create_price(400),
        quantity=1
    )
    assert sm.get_effective_price_info(source).price == source.shop.create_price(0)


@pytest.mark.django_db
def test_weight_limits():
    sm = ShippingMethod(tax_class=get_default_tax_class())
    sm.module_data = {"min_weight": "100", "max_weight": "500"}
    source = BasketishOrderSource(get_default_shop())
    assert any(ve.code == "min_weight" for ve in sm.get_validation_errors(source))
    source.add_line(type=OrderLineType.PRODUCT, weight=600)
    assert any(ve.code == "max_weight" for ve in sm.get_validation_errors(source))


@pytest.mark.django_db
def test_limited_methods():
    """
    Test that products can declare that they limit available shipping methods.
    """
    unique_shipping_method = ShippingMethod(tax_class=get_default_tax_class(), module_data={"price": 0})
    unique_shipping_method.save()
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
        ((unique_product.pk, impossible_product.pk,), ()),
        ((common_product.pk, impossible_product.pk,), ()),
    ]:
        product_ids = set(product_ids)
        assert ShippingMethod.objects.available_ids(shop=shop, products=product_ids) == set(method_ids)
