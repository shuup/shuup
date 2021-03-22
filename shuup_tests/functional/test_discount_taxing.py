# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import pytest
from collections import defaultdict
from decimal import Decimal
from django.test.utils import override_settings

from shuup.core.models import OrderLineType, Tax, TaxClass
from shuup.core.order_creator import OrderSource
from shuup.core.pricing import TaxlessPrice
from shuup.core.taxing import TaxSummary
from shuup.default_tax.models import TaxRule
from shuup.testing.factories import create_product, get_payment_method, get_shipping_method, get_shop
from shuup.utils import babel_precision_provider
from shuup.utils.money import Money, set_precision_provider
from shuup.utils.numbers import bankers_round


def setup_module(module):
    # uses the get_precision to avoid db hits
    set_precision_provider(babel_precision_provider.get_precision)

    global settings_overrider
    settings_overrider = override_settings(SHUUP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE=False)
    settings_overrider.__enter__()


def teardown_module(module):
    settings_overrider.__exit__(None, None, None)


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_1prod(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "product: P1      |price: 200.00|qty: 1|discount:  0.00|tax: A",
            "discount: SALE   |price: -20.00|qty: 1|discount: 20.00",
        ],
        tax_rates={"A": ["0.25"]},
    )
    source.calculate_taxes()

    assert source.total_price.value == 180
    assert get_price_by_tax_class(source) == {"TC-A": 200, "": -20}

    if taxes == "taxful":
        #    Name    Rate    Base amount     Tax amount         Taxful
        assert get_pretty_tax_summary(source) == ["Tax-A   0.25  144.000000000   36.000000000  180.000000000"]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            ["Tax-A   0.25  -16.000000000   -4.000000000  -20.000000000"]
        ]
    else:
        assert get_pretty_tax_summary(source) == ["Tax-A   0.25  180.000000000   45.000000000  225.000000000"]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            ["Tax-A   0.25  -20.000000000   -5.000000000  -25.000000000"]
        ]


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_2prods(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "product: P1      |price:  10.00|qty: 1|discount:  0.00|tax: A",
            "product: P2      |price:  20.00|qty: 1|discount:  0.00|tax: B",
            "discount: SALE   |price:  -3.00|qty: 1|discount:  3.00",
        ],
        tax_rates={"A": ["0.25"], "B": ["0.20"]},
    )
    source.calculate_taxes()

    assert source.total_price.value == 27
    assert get_price_by_tax_class(source) == {"TC-A": 10, "TC-B": 20, "": -3}

    if taxes == "taxful":
        #    Name    Rate    Base amount     Tax amount         Taxful
        assert get_pretty_tax_summary(source) == [
            "Tax-A   0.25    7.200000000    1.800000000    9.000000000",
            "Tax-B   0.20   15.000000000    3.000000000   18.000000000",
            "Total   0.22   22.200000000    4.800000000   27.000000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.25   -0.800000000   -0.200000000   -1.000000000",
                "Tax-B   0.20   -1.666666667   -0.333333333   -2.000000000",
            ]
        ]
    else:
        assert get_pretty_tax_summary(source) == [
            "Tax-A   0.25    9.000000000    2.250000000   11.250000000",
            "Tax-B   0.20   18.000000000    3.600000000   21.600000000",
            "Total   0.22   27.000000000    5.850000000   32.850000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.25   -1.000000000   -0.250000000   -1.250000000",
                "Tax-B   0.20   -2.000000000   -0.400000000   -2.400000000",
            ]
        ]


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_2prods_2taxrates(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "product: P1      |price:  10.00|qty: 1|discount:  0.00|tax: A",
            "product: P2      |price:  20.00|qty: 1|discount:  0.00|tax: B",
            "discount: SALE   |price:  -3.00|qty: 1|discount:  3.00",
        ],
        tax_rates={"A": ["0.20", "0.05"], "B": ["0.15", "0.05"]},
    )
    source.calculate_taxes()

    assert source.total_price.value == 27
    assert get_price_by_tax_class(source) == {"TC-A": 10, "TC-B": 20, "": -3}

    if taxes == "taxful":
        #    Name    Rate    Base amount     Tax amount         Taxful
        assert get_pretty_tax_summary(source) == [
            "Tax-A-1 0.20    7.200000000    1.440000000    8.640000000",
            "Tax-B-1 0.15   15.000000000    2.250000000   17.250000000",
            "Tax-A-2 0.05    7.200000000    0.360000000    7.560000000",
            "Tax-B-2 0.05   15.000000000    0.750000000   15.750000000",
            "Total   0.22   22.200000000    4.800000000   27.000000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A-1 0.20   -0.800000000   -0.160000000   -0.960000000",
                "Tax-A-2 0.05   -0.800000000   -0.040000000   -0.840000000",
                "Tax-B-1 0.15   -1.666666667   -0.250000000   -1.916666667",
                "Tax-B-2 0.05   -1.666666667   -0.083333333   -1.750000000",
            ]
        ]
    else:
        assert get_pretty_tax_summary(source) == [
            "Tax-A-1 0.20    9.000000000    1.800000000   10.800000000",
            "Tax-B-1 0.15   18.000000000    2.700000000   20.700000000",
            "Tax-A-2 0.05    9.000000000    0.450000000    9.450000000",
            "Tax-B-2 0.05   18.000000000    0.900000000   18.900000000",
            "Total   0.22   27.000000000    5.850000000   32.850000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A-1 0.20   -1.000000000   -0.200000000   -1.200000000",
                "Tax-A-2 0.05   -1.000000000   -0.050000000   -1.050000000",
                "Tax-B-1 0.15   -2.000000000   -0.300000000   -2.300000000",
                "Tax-B-2 0.05   -2.000000000   -0.100000000   -2.100000000",
            ]
        ]


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_3prods_with_services(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "product: P1      |price:  10.00|qty: 2|discount:  2.00|tax: A",
            "product: P2      |price:  40.00|qty: 8|discount:  0.00|tax: B",
            "product: P3      |price:  60.00|qty: 6|discount: 12.00|tax: C",
            "payment: Invoice |price:   2.50|qty: 1|discount:  0.00|tax: A",
            "shipping: Ship   |price:   7.50|qty: 1|discount:  0.00|tax: A",
            "discount: SALE   |price: -30.00|qty: 1|discount: 30.00",
        ],
        tax_rates={"A": ["0.25"], "B": ["0.15"], "C": ["0.30"]},
    )
    source.calculate_taxes()

    assert source.total_price.value == 90
    assert get_price_by_tax_class(source) == {"TC-A": 20, "TC-B": 40, "TC-C": 60, "": -30}

    if taxes == "taxful":
        #    Name    Rate    Base amount     Tax amount         Taxful
        assert get_pretty_tax_summary(source) == [
            "Tax-C   0.30   34.610000000   10.384615385   45.000000000",
            "Tax-A   0.25   12.000000000    3.000000000   15.000000000",
            "Tax-B   0.15   26.080000000    3.913043478   30.000000000",
            "Total   0.24   72.700000000   17.297658863   90.000000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.25   -4.000000000   -1.000000000   -5.000000000",
                "Tax-B   0.15   -8.695652174   -1.304347826  -10.000000000",
                "Tax-C   0.30  -11.538461538   -3.461538462  -15.000000000",
            ]
        ]
    else:
        assert get_pretty_tax_summary(source) == [
            "Tax-C   0.30   45.000000000   13.500000000   58.500000000",
            "Tax-A   0.25   15.000000000    3.750000000   18.750000000",
            "Tax-B   0.15   30.000000000    4.500000000   34.500000000",
            "Total   0.24   90.000000000   21.750000000  111.750000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.25   -5.000000000   -1.250000000   -6.250000000",
                "Tax-B   0.15  -10.000000000   -1.500000000  -11.500000000",
                "Tax-C   0.30  -15.000000000   -4.500000000  -19.500000000",
            ]
        ]


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_3prods_services_2discounts(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "product: P1      |price:  24.00|qty: 2|discount:  0.00|tax: A",
            "product: P2      |price: 100.00|qty: 8|discount:  0.00|tax: B",
            "product: P3      |price:  80.00|qty: 5|discount:  5.00|tax: C",
            "payment: Invoice |price:   6.25|qty: 1|discount:  0.00|tax: B",
            "shipping: Ship   |price:  18.75|qty: 1|discount:  2.50|tax: B",
            "discount: SALE1  |price: -22.90|qty: 1|discount: 22.90",
            "discount: SALE2  |price: -11.45|qty: 1|discount: 11.45",
        ],
        tax_rates={"A": ["0.25"], "B": ["0.20"], "C": ["0.50"]},
    )
    source.calculate_taxes()

    _check_taxful_price(source)
    _check_taxless_price(source)
    assert source.total_price.value == Decimal("194.65")
    assert get_price_by_tax_class(source) == {"TC-A": 24, "TC-B": 125, "TC-C": 80, "": Decimal("-34.35")}

    if taxes == "taxful":
        #    Name    Rate    Base amount     Tax amount         Taxful
        assert get_pretty_tax_summary(source) == [
            "Tax-C   0.50   45.330000000   22.666666667   68.000000000",
            "Tax-A   0.25   16.320000000    4.080000000   20.400000000",
            "Tax-B   0.20   88.530000000   17.708333333  106.250000000",
            "Total   0.30  150.180000000   44.455000000  194.650000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.25   -1.920000000   -0.480000000   -2.400000000",
                "Tax-B   0.20  -10.416666667   -2.083333333  -12.500000000",
                "Tax-C   0.50   -5.333333333   -2.666666667   -8.000000000",
            ],
            [
                "Tax-A   0.25   -0.960000000   -0.240000000   -1.200000000",
                "Tax-B   0.20   -5.208333333   -1.041666667   -6.250000000",
                "Tax-C   0.50   -2.666666667   -1.333333333   -4.000000000",
            ],
        ]
    else:
        assert get_pretty_tax_summary(source) == [
            "Tax-C   0.50   68.000000000   34.000000000  102.000000000",
            "Tax-A   0.25   20.400000000    5.100000000   25.500000000",
            "Tax-B   0.20  106.250000000   21.250000000  127.500000000",
            "Total   0.31  194.650000000   60.350000000  255.000000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.25   -2.400000000   -0.600000000   -3.000000000",
                "Tax-B   0.20  -12.500000000   -2.500000000  -15.000000000",
                "Tax-C   0.50   -8.000000000   -4.000000000  -12.000000000",
            ],
            [
                "Tax-A   0.25   -1.200000000   -0.300000000   -1.500000000",
                "Tax-B   0.20   -6.250000000   -1.250000000   -7.500000000",
                "Tax-C   0.50   -4.000000000   -2.000000000   -6.000000000",
            ],
        ]


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_3prods_services_2discounts2(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "product: P1      |price:  30.00|qty: 2|discount:  0.00|tax: A",
            "product: P2      |price: 120.00|qty: 8|discount:  0.00|tax: B",
            "product: P3      |price: 120.00|qty: 5|discount:  5.00|tax: C",
            "payment: Invoice |price:   7.50|qty: 1|discount:  0.00|tax: B",
            "shipping: Ship   |price:  22.50|qty: 1|discount:  2.50|tax: B",
            "discount: SALE1  |price: -30.00|qty: 1|discount: 30.00",
            "discount: SALE2  |price: -15.00|qty: 1|discount: 15.00",
        ],
        tax_rates={"A": ["0.25"], "B": ["0.20"], "C": ["0.50"]},
    )
    source.calculate_taxes()

    _check_taxful_price(source)
    _check_taxless_price(source)
    assert source.total_price.value == 255
    assert get_price_by_tax_class(source) == {"TC-A": 30, "TC-B": 150, "TC-C": 120, "": -45}

    if taxes == "taxful":
        #    Name    Rate    Base amount     Tax amount         Taxful
        assert get_pretty_tax_summary(source) == [
            "Tax-C   0.50   68.000000000   34.000000000  102.000000000",
            "Tax-A   0.25   20.400000000    5.100000000   25.500000000",
            "Tax-B   0.20  106.250000000   21.250000000  127.500000000",
            "Total   0.31  194.650000000   60.350000000  255.000000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.25   -2.400000000   -0.600000000   -3.000000000",
                "Tax-B   0.20  -12.500000000   -2.500000000  -15.000000000",
                "Tax-C   0.50   -8.000000000   -4.000000000  -12.000000000",
            ],
            [
                "Tax-A   0.25   -1.200000000   -0.300000000   -1.500000000",
                "Tax-B   0.20   -6.250000000   -1.250000000   -7.500000000",
                "Tax-C   0.50   -4.000000000   -2.000000000   -6.000000000",
            ],
        ]
    else:
        assert get_pretty_tax_summary(source) == [
            "Tax-C   0.50  102.000000000   51.000000000  153.000000000",
            "Tax-A   0.25   25.500000000    6.375000000   31.880000000",
            "Tax-B   0.20  127.500000000   25.500000000  153.000000000",
            "Total   0.32  255.000000000   82.875000000  337.870000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.25   -3.000000000   -0.750000000   -3.750000000",
                "Tax-B   0.20  -15.000000000   -3.000000000  -18.000000000",
                "Tax-C   0.50  -12.000000000   -6.000000000  -18.000000000",
            ],
            [
                "Tax-A   0.25   -1.500000000   -0.375000000   -1.875000000",
                "Tax-B   0.20   -7.500000000   -1.500000000   -9.000000000",
                "Tax-C   0.50   -6.000000000   -3.000000000   -9.000000000",
            ],
        ]


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_all_discounted(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "product: P1      |price:  30.00|qty: 1|discount:  0.00|tax: A",
            "product: P2      |price:  60.00|qty: 1|discount:  0.00|tax: B",
            "discount: SALE   |price: -90.00|qty: 1|discount: 90.00",
        ],
        tax_rates={"A": ["0.20"], "B": ["0.10"]},
    )
    source.calculate_taxes()

    _check_taxful_price(source)
    _check_taxless_price(source)
    assert source.total_price.value == 0
    assert get_price_by_tax_class(source) == {"TC-A": 30, "TC-B": 60, "": -90}

    if taxes == "taxful":
        #    Name    Rate    Base amount     Tax amount         Taxful
        assert get_pretty_tax_summary(source) == [
            "Tax-A   0.20    0.000000000    0.000000000    0.000000000",
            "Tax-B   0.10    0.000000000    0.000000000    0.000000000",
            "Total   0.00    0.000000000    0.000000000    0.000000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.20  -25.000000000   -5.000000000  -30.000000000",
                "Tax-B   0.10  -54.545454545   -5.454545455  -60.000000000",
            ]
        ]
    else:
        assert get_pretty_tax_summary(source) == [
            "Tax-A   0.20    0.000000000    0.000000000    0.000000000",
            "Tax-B   0.10    0.000000000    0.000000000    0.000000000",
            "Total   0.00    0.000000000    0.000000000    0.000000000",
        ]
        assert get_pretty_line_taxes_of_discount_lines(source) == [
            [
                "Tax-A   0.20  -30.000000000   -6.000000000  -36.000000000",
                "Tax-B   0.10  -60.000000000   -6.000000000  -66.000000000",
            ]
        ]


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_zero_priced_products(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "product: P1      |price:   0.00|qty: 1|discount:  0.00|tax: A",
            "product: P2      |price:   0.00|qty: 1|discount:  0.00|tax: B",
            "discount: Foobar |price:  10.00|qty: 1|discount:-10.00",
        ],
        tax_rates={"A": ["0.25"], "B": ["0.20"]},
    )
    source.calculate_taxes()

    _check_taxful_price(source)
    _check_taxless_price(source)
    assert source.total_price.value == 10
    assert get_price_by_tax_class(source) == {"TC-A": 0, "TC-B": 0, "": 10}

    #    Name    Rate    Base amount     Tax amount         Taxful
    assert get_pretty_tax_summary(source) == [
        "Tax-A   0.25    0.000000000    0.000000000    0.000000000",
        "Tax-B   0.20    0.000000000    0.000000000    0.000000000",
        "Untaxed 0.00   10.000000000    0.000000000   10.000000000",
        "Total   0.00   10.000000000    0.000000000   10.000000000",
    ]
    assert get_pretty_line_taxes_of_discount_lines(source) == [[]]


@pytest.mark.django_db
@pytest.mark.parametrize("taxes", ["taxful", "taxless"])
def test_no_products(taxes):
    source = create_order_source(
        prices_include_tax=(taxes == "taxful"),
        line_data=[
            "discount: Foobar |price:  50.00|qty: 1|discount:-50.00",
            "discount: SALE   |price: -10.00|qty: 1|discount: 10.00",
        ],
        tax_rates={},
    )
    source.calculate_taxes()

    _check_taxful_price(source)
    _check_taxless_price(source)
    assert source.total_price.value == 40
    assert get_price_by_tax_class(source) == {"": 40}

    #    Name    Rate    Base amount     Tax amount         Taxful
    assert get_pretty_tax_summary(source) == ["Untaxed 0.00   40.000000000    0.000000000   40.000000000"]
    assert get_pretty_line_taxes_of_discount_lines(source) == [[], []]


# ================================================================
# Creating test data
# ================================================================


class Line(object):
    def __init__(self, price, quantity=1, discount=0, **kwargs):
        self.price = Decimal(price)
        self.quantity = Decimal(quantity)
        self.discount = Decimal(discount)
        self.__dict__.update(kwargs)
        self.base_unit_price = (self.price + self.discount) / self.quantity
        self.is_product = "product_sku" in kwargs
        self.is_payment = "payment_name" in kwargs
        self.is_shipping = "shipping_name" in kwargs
        self.is_discount = "discount_text" in kwargs

    @classmethod
    def from_text(cls, text):
        preparsed = (item.split(":") for item in text.split("|"))
        data = {x[0].strip(): x[1].strip() for x in preparsed}
        mappings = [
            ("product", "product_sku"),
            ("payment", "payment_name"),
            ("shipping", "shipping_name"),
            ("discount", "discount_text"),
            ("qty", "quantity"),
            ("disc", "discount"),
            ("tax", "tax_name"),
        ]
        for (old_key, new_key) in mappings:
            if old_key in data:
                data[new_key] = data[old_key]
                del data[old_key]
        return cls(**data)


def create_order_source(prices_include_tax, line_data, tax_rates):
    """
    Get order source with some testing data.

    :rtype: OrderSource
    """
    lines = [Line.from_text(x) for x in line_data]
    shop = get_shop(prices_include_tax, currency="USD")
    tax_classes = create_assigned_tax_classes(tax_rates)
    products = create_products(shop, lines, tax_classes)
    services = create_services(shop, lines, tax_classes)

    source = OrderSource(shop)
    fill_order_source(source, lines, products, services)
    return source


def create_assigned_tax_classes(tax_rates):
    return {
        tax_name: create_assigned_tax_class(tax_name, rates_to_assign)
        for (tax_name, rates_to_assign) in tax_rates.items()
    }


def create_assigned_tax_class(name, rates_to_assign):
    """
    Create a tax class and assign taxes for it with tax rules.
    """
    tax_class = TaxClass.objects.create(name="TC-%s" % name)
    for (n, tax_rate) in enumerate(rates_to_assign, 1):
        tax_name = "Tax-%s" % name if len(rates_to_assign) == 1 else "Tax-%s-%d" % (name, n)
        tax = Tax.objects.create(rate=tax_rate, name=tax_name)
        TaxRule.objects.create(tax=tax).tax_classes.add(tax_class)
    return tax_class


def create_products(shop, lines, tax_classes):
    return {
        line.product_sku: create_product(
            line.product_sku, shop, default_price=line.base_unit_price, tax_class=tax_classes[line.tax_name]
        )
        for line in lines
        if line.is_product
    }


def create_services(shop, lines, tax_classes):
    def service_name(line):
        return "payment_method" if line.is_payment else "shipping_method"

    return {
        service_name(line): create_service(shop, line, tax_classes)
        for line in lines
        if (line.is_payment or line.is_shipping)
    }


def create_service(shop, line, tax_classes):
    assert line.quantity == 1 and line.discount == 0
    if line.is_payment:
        meth = get_payment_method(shop=shop, price=line.price, name=line.payment_name)
    elif line.is_shipping:
        meth = get_shipping_method(shop=shop, price=line.price, name=line.shipping_name)
    meth.tax_class = tax_classes[line.tax_name]
    meth.save()
    return meth


def fill_order_source(source, lines, products, services):
    for line in lines:
        if line.is_product:
            source.add_line(
                product=products[line.product_sku],
                quantity=line.quantity,
                base_unit_price=source.create_price(line.base_unit_price),
                discount_amount=source.create_price(line.discount),
            )
        elif line.is_payment:
            source.payment_method = services["payment_method"]
        elif line.is_shipping:
            source.shipping_method = services["shipping_method"]
        elif line.is_discount:
            source.add_line(
                type=OrderLineType.DISCOUNT,
                quantity=line.quantity,
                base_unit_price=source.create_price(line.base_unit_price),
                discount_amount=source.create_price(line.discount),
                text=line.discount_text,
            )


# ================================================================
# Getting and formatting results
# ================================================================


def get_price_by_tax_class(source):
    price_by_tax_class = defaultdict(Decimal)
    for line in source.get_final_lines(with_taxes=False):
        tax_class_name = line.tax_class.name if line.tax_class else ""
        price_by_tax_class[tax_class_name] += line.price.value
    return price_by_tax_class


TAX_DISTRIBUTION_LINE_FORMAT = "{n:7s} {r:4.2f} {ba:14.9f} {a:14.9f} {t:14.9f}"


def get_pretty_tax_summary(source):
    summary = get_tax_summary(source)
    lines = [
        TAX_DISTRIBUTION_LINE_FORMAT.format(
            n=line.tax_name, r=line.tax_rate, ba=line.based_on, a=line.tax_amount, t=line.taxful
        )
        for line in summary
    ]
    total_base = source.taxless_total_price.value
    total_taxful = source.taxful_total_price.value
    total_tax_amount = sum(x.tax_amount.value for x in summary)  # Like it was read from db
    total_line = TAX_DISTRIBUTION_LINE_FORMAT.format(
        n="Total",
        r=((total_tax_amount / total_base) if abs(total_base) > 0.0001 else 0),
        ba=total_base,
        a=total_tax_amount,
        t=total_taxful,
    )
    return lines + ([total_line] if len(summary) > 1 else [])


def get_tax_summary(source):
    """
    Get tax summary of given source lines.

    :type source: OrderSource
    :type lines: list[SourceLine]
    :rtype: TaxSummary
    """
    all_line_taxes = []
    untaxed = TaxlessPrice(source.create_price(0).amount)
    for line in source.get_final_lines():
        line_taxes = list(line.taxes)
        all_line_taxes.extend(line_taxes)
        if not line_taxes:
            untaxed += line.taxless_price
    return TaxSummary.from_line_taxes(all_line_taxes, untaxed)


def get_pretty_line_taxes_of_discount_lines(source):
    return [prettify_line_taxes(line) for line in source.get_final_lines() if line.tax_class is None]


def prettify_line_taxes(line):
    return [
        TAX_DISTRIBUTION_LINE_FORMAT.format(
            n=line_tax.name,
            r=line_tax.rate,
            ba=line_tax.base_amount,
            a=line_tax.amount,
            t=(line_tax.base_amount + line_tax.amount),
        )
        for line_tax in sorted(line.taxes, key=(lambda x: x.name))
    ]


def _check_taxless_price(source):
    for line in source.get_lines():
        from_components = bankers_round(line.taxless_base_unit_price * line.quantity - line.taxless_discount_amount, 2)
        assert from_components == line.taxless_price
        assert line.price == line.base_unit_price * line.quantity - line.discount_amount
        assert line.price == line.base_unit_price * line.quantity - line.discount_amount
        assert line.discount_amount == line.base_price - line.price
        if line.base_price:
            assert line.discount_rate == (1 - (line.price / line.base_price))
            assert line.discount_percentage == 100 * (1 - (line.price / line.base_price))
        if line.quantity:
            assert line.unit_discount_amount == line.discount_amount / line.quantity


def _check_taxful_price(source):
    for line in source.get_lines():
        from_components = bankers_round(line.taxful_base_unit_price * line.quantity - line.taxful_discount_amount, 2)
        assert from_components == line.taxful_price
        assert line.price == line.base_unit_price * line.quantity - line.discount_amount
        assert line.discount_amount == line.base_price - line.price
        if line.base_price:
            assert line.discount_rate == (1 - (line.price / line.base_price))
            assert line.discount_percentage == 100 * (1 - (line.price / line.base_price))
        if line.quantity:
            assert line.unit_discount_amount == line.discount_amount / line.quantity
