# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from mock import patch

from shoop.utils.money import Money


def test_money_init_does_not_call_settings():
    def guarded_getattr(self, name):
        assert False, 'nobody should read settings yet'

    with patch.object(type(settings), '__getattr__', guarded_getattr):
        Money(42)


def test_money_default_currency():
    m = Money(42)
    assert m.currency == settings.SHOOP_HOME_CURRENCY


def test_units_match():
    class XxxMoney(int):
        currency = 'XXX'

    m1 = Money(1)
    m2 = Money(2)
    m3 = Money(3)
    m3._currency = 'XXX'
    m4 = XxxMoney(4)

    assert m1.unit_matches_with(m2)
    assert not m1.unit_matches_with(m3)
    assert m3.unit_matches_with(m4)
