# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

from django.test.utils import override_settings
import pytest
from shoop.apps.provides import override_provides
from shoop.core.models import Address, OrderLineType
from shoop.core.order_creator.source import OrderSource, SourceLine
from shoop.core.pricing import TaxfulPrice, TaxlessPrice
from shoop.core.taxing import TaxModule
from shoop.core.taxing.utils import stacked_value_added_taxes
from shoop.testing.factories import get_tax


class IrvineCaliforniaTaxation(TaxModule):
    identifier = "irvine"
    def get_line_taxes(self, source_line):
        taxes = []
        if source_line.source.billing_address.postal_code == "92602":
            taxes = [
                # Based on data from TaxJar
                get_tax("CA", "California", rate="0.065"),
                get_tax("CA-OC", "Orange County", rate="0.01"),
                get_tax("CA-OC-IR", "Irvine", rate="0.00"),
                get_tax("CA-OC-IR-DS", "District tax", rate="0.005"),
            ]
        return stacked_value_added_taxes(source_line.total_price, taxes).taxes


@pytest.mark.django_db
def test_stacked_tax_taxless_price():
    source = OrderSource()
    source.lines = [
        SourceLine(source=source, type=OrderLineType.OTHER, quantity=1, unit_price=TaxlessPrice(10))
    ]
    with override_provides("tax_module", ["shoop_tests.functional.test_tax_system:IrvineCaliforniaTaxation"]):
        with override_settings(SHOOP_TAX_MODULE="irvine"):
            source.billing_address = Address(
                street="16215 Alton Pkwy",
                postal_code="92602",
            )
            line = source.get_final_lines()[0]
            assert isinstance(line, SourceLine)
            assert line.taxes
            assert line.taxful_total_price.amount == Decimal("10.800")
            source.uncache()

            # Let's move out to a taxless location.
            source.billing_address.postal_code = "11111"
            line = source.get_final_lines()[0]
            assert isinstance(line, SourceLine)
            assert not line.taxes
            assert line.taxful_total_price.amount == Decimal("10")


@pytest.mark.django_db
def test_stacked_tax_taxful_price():
    source = OrderSource()
    source.lines = [
        SourceLine(source=source, type=OrderLineType.OTHER, quantity=1, unit_price=TaxfulPrice(20))
    ]
    with override_provides("tax_module", ["shoop_tests.functional.test_tax_system:IrvineCaliforniaTaxation"]):
        with override_settings(SHOOP_TAX_MODULE="irvine"):
            source.billing_address = Address(
                street="16215 Alton Pkwy",
                postal_code="92602",
            )
            line = source.get_final_lines()[0]
            assert isinstance(line, SourceLine)
            assert line.taxes
            assert line.taxful_total_price == TaxfulPrice(20)
            assert abs(line.taxless_total_price.amount - Decimal("18.519")) < Decimal("0.01")
            source.uncache()

            # Let's move out to a taxless location.
            source.billing_address.postal_code = "11111"
            line = source.get_final_lines()[0]
            assert isinstance(line, SourceLine)
            assert not line.taxes
            assert line.taxful_total_price == TaxfulPrice(20)
            assert line.taxless_total_price.amount == Decimal("20")
