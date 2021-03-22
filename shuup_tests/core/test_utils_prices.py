# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from decimal import Decimal
from django.conf import settings
from django.test.client import RequestFactory

from shuup.apps.provides import override_provides
from shuup.core.models import AnonymousContact, Product, Shop, Tax, TaxClass
from shuup.core.pricing import PriceInfo, TaxfulPrice, TaxlessPrice
from shuup.core.taxing import SourceLineTax, TaxedPrice, TaxModule
from shuup.core.utils.prices import convert_taxness
from shuup.testing.factories import get_currency
from shuup.utils import babel_precision_provider
from shuup.utils.money import Money, set_precision_provider

TAX_MODULE_SPEC = __name__ + ":DummyTaxModule"

original_tax_module = settings.SHUUP_TAX_MODULE
tax_mod_overrider = override_provides("tax_module", [TAX_MODULE_SPEC])


def setup_module(module):
    settings.SHUUP_TAX_MODULE = "dummy_tax_module"
    tax_mod_overrider.__enter__()

    # uses the get_precision to avoid db hits
    set_precision_provider(babel_precision_provider.get_precision)


def teardown_module(module):
    tax_mod_overrider.__exit__(None, None, None)
    settings.SHUUP_TAX_MODULE = original_tax_module


class DummyTaxModule(TaxModule):
    calculations_done = 0

    identifier = "dummy_tax_module"

    def get_taxed_price(self, context, price, tax_class):
        if price.includes_tax:
            taxful = price
            taxless = TaxlessPrice(price.amount / Decimal("1.2"))
        else:
            taxful = TaxfulPrice(price.amount * Decimal("1.2"))
            taxless = price
        tax_amount = taxful.amount - taxless.amount
        base_amount = taxless.amount
        taxes = [
            SourceLineTax(Tax(), "fifth", tax_amount, base_amount),
        ]
        DummyTaxModule.calculations_done += 1
        return TaxedPrice(taxful, taxless, taxes)


@pytest.mark.parametrize(
    "taxes,price_cls",
    [
        (None, TaxfulPrice),
        (None, TaxlessPrice),
        (False, TaxlessPrice),
        (True, TaxfulPrice),
    ],
)
def test_convert_taxness_without_conversion(taxes, price_cls):
    request = get_request()
    item = Product()
    priceful = _get_price_info(price_cls)
    calcs_done_before = DummyTaxModule.calculations_done
    result = convert_taxness(request, item, priceful, with_taxes=taxes)
    calcs_done_after = DummyTaxModule.calculations_done
    assert result == priceful
    assert result.price == price_cls(480, "USD")
    assert result.base_price == price_cls(660, "USD")
    assert result.quantity == 2
    assert calcs_done_after == calcs_done_before


def test_convert_taxness_taxless_to_taxful():
    request = get_request()
    tax_class = TaxClass()
    item = Product(tax_class=tax_class)
    priceful = _get_price_info(TaxlessPrice)
    calcs_done_before = DummyTaxModule.calculations_done
    result = convert_taxness(request, item, priceful, with_taxes=True)
    calcs_done_after = DummyTaxModule.calculations_done
    assert result != priceful
    assert result.price == TaxfulPrice(576, "USD")
    assert result.base_price == TaxfulPrice(792, "USD")
    assert result.quantity == 2
    assert result.tax_amount == Money(96, "USD")
    assert result.taxful_price == result.price
    assert result.taxless_price == priceful.price
    assert calcs_done_after == calcs_done_before + 2


def test_convert_taxness_taxful_to_taxless():
    request = get_request()
    tax_class = TaxClass()
    item = Product(tax_class=tax_class)
    priceful = _get_price_info(TaxfulPrice)
    calcs_done_before = DummyTaxModule.calculations_done
    result = convert_taxness(request, item, priceful, with_taxes=False)
    calcs_done_after = DummyTaxModule.calculations_done
    assert result != priceful
    assert (result.price - TaxlessPrice(400, "USD")).value < 0.00001
    assert result.base_price == TaxlessPrice(550, "USD")
    assert result.quantity == 2
    assert result.tax_amount == Money(80, "USD")
    assert result.taxless_price == result.price
    assert result.taxful_price == priceful.price
    assert calcs_done_after == calcs_done_before + 2


def get_request():
    request = RequestFactory().get("/")
    request.shop = Shop(currency="USD", prices_include_tax=False)
    request.customer = AnonymousContact()
    request.person = request.customer


def _get_price_info(price_cls, quantity=2):
    price = quantity * price_cls(240, "USD")
    base_price = quantity * price_cls(330, "USD")
    return PriceInfo(price, base_price, quantity)
