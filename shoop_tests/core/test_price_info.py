# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.core.pricing import TaxlessPrice
from shoop.core.pricing.price_info import PriceInfo


def test_price_info_no_discount():
    pi = PriceInfo(price=TaxlessPrice(100), base_price=TaxlessPrice(100))
    assert not pi.is_discounted
    assert pi.discount_percentage == 0
    assert pi.discount_amount == TaxlessPrice(0)


def test_price_info_discounts():
    pi = PriceInfo(price=TaxlessPrice(75), base_price=TaxlessPrice(100))
    assert pi.is_discounted
    assert pi.discount_percentage == 25
    assert pi.discount_amount == TaxlessPrice(25)
