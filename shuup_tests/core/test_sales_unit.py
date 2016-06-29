# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from decimal import Decimal

from shuup.core.models import SalesUnit


def test_sales_unit_decimals():
    assert SalesUnit(decimals=0).quantity_step == 1
    assert not SalesUnit(decimals=0).allow_fractions
    assert SalesUnit(decimals=1).quantity_step == Decimal("0.1")
    assert SalesUnit(decimals=1).allow_fractions
    assert SalesUnit(decimals=10).quantity_step == Decimal("0.0000000001")
    assert SalesUnit(decimals=2).round("1.509") == Decimal("1.51")
    assert SalesUnit(decimals=0).round("1.5") == Decimal("2")
