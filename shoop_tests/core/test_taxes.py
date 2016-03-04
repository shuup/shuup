# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from django.test.utils import override_settings
from django.utils.translation import activate

from shoop.core.models import CustomerTaxGroup, OrderLineType
from shoop.core.order_creator import TaxesNotCalculated
from shoop.testing.factories import (
    get_default_product, get_default_shop, get_default_supplier,
)
from shoop_tests.utils.basketish_order_source import BasketishOrderSource


@pytest.mark.django_db
def test_customertaxgroup():
    activate("en")
    person_group = CustomerTaxGroup.get_default_person_group()
    assert CustomerTaxGroup.objects.count() == 1
    assert person_group.identifier == "default_person_customers"
    assert person_group.name == "Retail Customers"

    company_group = CustomerTaxGroup.get_default_company_group()
    assert CustomerTaxGroup.objects.count() == 2
    assert company_group.identifier == "default_company_customers"
    assert company_group.name == "Company Customers"


def get_source():
    source = BasketishOrderSource(get_default_shop())
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )
    return source


@pytest.mark.django_db
def test_calculate_taxes_automatically_setting():
    with override_settings(SHOOP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE=True):
        source = get_source()
        source.get_final_lines()
        assert source._taxes_calculated == True

        source = get_source()
        assert source._taxes_calculated == False
        source.calculate_taxes_or_raise()
        assert source._taxes_calculated == True


    with override_settings(SHOOP_CALCULATE_TAXES_AUTOMATICALLY_IF_POSSIBLE=False):
        source = get_source()
        source.get_final_lines()
        assert source._taxes_calculated == False

        with pytest.raises(TaxesNotCalculated):
            source.calculate_taxes_or_raise()
