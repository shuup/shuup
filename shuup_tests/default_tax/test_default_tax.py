# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import random
from decimal import Decimal

import pytest
from django.test.utils import override_settings

from shuup.core.models import Tax, TaxClass
from shuup.core.taxing import get_tax_module, TaxingContext
from shuup.default_tax.admin_module.views import TaxRuleEditView
from shuup.default_tax.models import TaxRule
from shuup.default_tax.module import (
    DefaultTaxModule, get_taxes_of_effective_rules
)
from shuup.testing.factories import create_product, get_default_shop, get_shop
from shuup.testing.utils import apply_request_middleware
from shuup.utils.money import Money
from shuup_tests.utils.forms import get_form_data


class RuleDef(object):
    def __init__(
            self, tax, countries, regions, postals,
            priority=0, override_group=0):
        self.data = locals()

    def get_tax_rule(self):
        return TaxRule(
            country_codes_pattern=self.data['countries'],
            region_codes_pattern=self.data['regions'],
            postal_codes_pattern=self.data['postals'],
            priority=self.data['priority'],
            override_group=self.data['override_group'],
            tax=create_tax_from_string(self.data['tax']),
        )


TAX_RULE_DEFS = [
    RuleDef('0% ZZ', 'XX', 'ZZ*', '', override_group=999),
    RuleDef('0% Z', 'XX', 'Z*', '', override_group=99),
    RuleDef('24% FI-ALV', 'FI', '', ''),
    RuleDef('6.5% CA', 'US', 'CA', ''),
    RuleDef('1% CA-OC', 'US', 'CA', '90600-92899'),
    RuleDef('0% CA-OC-IR', 'US', 'CA', '92602'),
    RuleDef('0.5% CA-OC-IR-DS', 'US', 'CA', '92602'),
    RuleDef('5% GST', 'CA', 'AB,BC,MB,NT,NU,QC,SK,YT', '', priority=0),
    RuleDef('5% PST5', 'CA', 'SK', '', priority=0),
    RuleDef('10% PST10', 'CA', 'QC', '', priority=1),
    RuleDef('50% 1A', 'XX', 'A', '', priority=1),
    RuleDef('20% 1B', 'XX', 'A,B', '', priority=1),
    RuleDef('30% 1C', 'XX', 'A-C', '', priority=1),
    RuleDef('50% 2A', 'XX', 'A', '', priority=2),
    RuleDef('50% 2B', 'XX', 'A-B', '', priority=2),
    RuleDef('$30 3*', 'XX', '*', '', priority=3),
    RuleDef('50% 4', 'XX', '', '', priority=4),
]


class Address(object):
    def __init__(self, country, region, postal):
        self.country_code = country
        self.region_code = region
        self.postal_code = postal


EXPECTED_TAXES_BY_ADDRESS = [
    (Address('FI', '', '20100'), ('FI-ALV',)),
    (Address('US', 'CA', '92602'), ('CA CA-OC CA-OC-IR CA-OC-IR-DS',)),
    (Address('US', 'CA', '92666'), ('CA CA-OC',)),
    (Address('US', 'CA', '90000'), ('CA',)),
    (Address('CA', 'QC', ''), ('GST', 'PST10',)),
    (Address('CA', 'SK', ''), ('GST PST5',)),
    (Address('CA', 'YT', ''), ('GST',)),
    (Address('XX', 'A', ''), ('1A 1B 1C', '2A 2B', '3*', '4',)),
    (Address('XX', 'B', ''), ('1B 1C', '2B', '3*', '4',)),
    (Address('XX', 'C', ''), ('1C', '3*', '4',)),
    (Address('XX', 'Y', ''), ('3*', '4',)),
    (Address('XX', 'Z', ''), ('Z',)),
    (Address('XX', 'ZX', ''), ('Z',)),
    (Address('XX', 'ZZ', ''), ('ZZ',)),
    (Address('XX', 'ZZ2', ''), ('ZZ',)),
    (Address('AA', '', ''), ()),
]


@pytest.mark.parametrize("address, expected_taxes", EXPECTED_TAXES_BY_ADDRESS)
def test_get_taxes_of_effective_rules(address, expected_taxes):
    context = TaxingContext(location=address)
    tax_rules = [ruledef.get_tax_rule() for ruledef in TAX_RULE_DEFS]
    result = get_taxes_of_effective_rules(context, tax_rules)
    grouped_codes_of_result = [[x.code for x in group] for group in result]
    expected_codes = [x.split() for x in expected_taxes]
    assert grouped_codes_of_result == expected_codes


TAX_AMOUNTS = {  # taxes for $1000
    ('FI-ALV',): 240,
    ('CA CA-OC CA-OC-IR CA-OC-IR-DS',): 80,
    ('CA CA-OC',): 75,
    ('CA',): 65,
    ('GST', 'PST10',): 155,
    ('GST PST5',): 100,
    ('GST',): 50,
    ('1A 1B 1C', '2A 2B', '3*', '4',): 5045,
    ('1B 1C', '2B', '3*', '4',): 2420,
    ('1C', '3*', '4',): 995,
    ('3*', '4',): 545,
    ('Z',): 0,
    ('ZZ',): 0,
    (): 0,
}


@pytest.mark.django_db
@pytest.mark.parametrize("address, expected_taxes", EXPECTED_TAXES_BY_ADDRESS)
def test_module(address, expected_taxes):
    """
    Test the DefaultTaxModule.
    """
    # Create a product
    shop = get_shop(prices_include_tax=False, currency='USD')
    product = create_product('PROD', shop=shop, default_price=1000)
    price = product.get_shop_instance(shop).default_price

    # Put the tax rules into database
    for ruledef in shuffled(TAX_RULE_DEFS):
        rule = ruledef.get_tax_rule()
        rule.tax.save()
        rule.tax = rule.tax  # refresh the id
        rule.save()
        rule.tax_classes.add(product.tax_class)
    assert TaxRule.objects.count() == len(TAX_RULE_DEFS)

    with override_settings(SHUUP_TAX_MODULE='default_tax'):
        module = get_tax_module()
        assert isinstance(module, DefaultTaxModule)

        context = TaxingContext(location=address)
        taxed_price = module.get_taxed_price_for(context, product, price)
        expected_codes = set(sum([x.split() for x in expected_taxes], []))
        assert set(x.tax.code for x in taxed_price.taxes) == expected_codes
        expected_tax = Money(TAX_AMOUNTS[expected_taxes], 'USD')
        assert taxed_price.taxful.amount == price.amount + expected_tax

    # Clean-up the rules
    TaxRule.objects.all().delete()


@pytest.mark.django_db
def test_rule_min_max():
    tax = create_tax("test-1", rate=Decimal("0.12"))
    tax.save()
    postals = "99501-99511,99513-99524,99529-99530,99540,99590,99550,99558,99567,99573,99577,99586-99588"

    rule = TaxRule.objects.create(postal_codes_pattern=postals, tax=tax)
    # rule.save()
    assert rule._postal_codes_min == "99501"
    assert rule._postal_codes_max == "99590"

    TaxRule.objects.create(postal_codes_pattern="12345,45600,80008,99999,10011", tax=tax)
    TaxRule.objects.create(postal_codes_pattern="10000-99999", tax=tax)
    TaxRule.objects.create(postal_codes_pattern="99506-99999", tax=tax)
    TaxRule.objects.create(postal_codes_pattern="99000-99001", tax=tax)

    postal_code = "99510"
    assert TaxRule.objects.may_match_postal_code(postal_code).count() == 4

    rule.postal_codes_pattern = "20320,!20100"
    rule.save()
    assert not rule._postal_codes_min
    assert not rule._postal_codes_max
    assert TaxRule.objects.may_match_postal_code(postal_code).count() == 4 # it still may match

    postal_code = None
    assert TaxRule.objects.may_match_postal_code(postal_code).count() == 1

@pytest.mark.django_db
def test_wildcard_postalcode():
    tax = create_tax("test-1", rate=Decimal("0.12"))
    tax.save()
    rule = TaxRule.objects.create(postal_codes_pattern="*", tax=tax)

    for postal_code in ["", None, "12333", "test"]:
        assert TaxRule.objects.may_match_postal_code(postal_code).count() == 1

    rule.postal_codes_pattern = ""
    rule.save()

    assert rule._postal_codes_min is None
    assert rule._postal_codes_max is None


@pytest.mark.django_db
def test_rule_admin(rf, admin_user):
    shop = get_default_shop()

    tax = create_tax("test-1", rate=Decimal("0.12"))
    tax.save()

    tax_class = TaxClass.objects.create(name="test")

    view = TaxRuleEditView(request=apply_request_middleware(rf.get("/"), user=admin_user))
    form_class = view.get_form_class()
    form_kwargs = view.get_form_kwargs()
    form = form_class(**form_kwargs)
    data = get_form_data(form)
    data.update({
        "shop": shop.pk,
        "postal_codes_pattern": "99501-99511,99513-99524,99529-99530,99540,99590,99550,99567,99573,99577,99586-99588",
        "country_codes_pattern": "FI,CA,US,SE",
        "region_codes_pattern": "CA,AR,IA,AK,WY,TN",
        "tax": tax.id,
        "tax_classes": [tax_class.id]
    })
    form = form_class(**dict(form_kwargs, data=data))
    form.full_clean()

    assert not form.errors

    rule = form.save()

    assert rule._postal_codes_min == "99501"
    assert rule._postal_codes_max == "99590"

    postal_code = "99510"
    assert TaxRule.objects.may_match_postal_code(postal_code).count() == 1

    postal_code = "99500"
    assert not TaxRule.objects.may_match_postal_code(postal_code).count()


def create_tax_from_string(string):
    if ' ' in string:
        (spec, name) = string.split(' ', 1)
    else:
        name = spec = string
    if spec.startswith('$'):
        return create_tax(name, amount=Money(spec[1:], 'USD'))
    elif spec.endswith('%'):
        return create_tax(name, rate=(Decimal(spec[:-1]) / 100))
    raise ValueError('Unknown tax string: %r' % (string,))


def create_tax(code, rate=None, amount=None):
    return Tax(code=code, name=('Tax ' + code), rate=rate, amount=amount)


def shuffled(iterable):
    items = list(iterable)
    random.shuffle(items)
    return items
