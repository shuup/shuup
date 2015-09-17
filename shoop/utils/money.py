# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings

from . import numbers


class Money(numbers.UnitedDecimal):
    def __new__(cls, value="0", currency=None, *args, **kwargs):
        assert currency is None, "currency support is not yet implemented"
        instance = super(Money, cls).__new__(cls, value, *args, **kwargs)
        instance._currency = currency
        return instance

    @property
    def currency(self):
        return (self._currency or settings.SHOOP_HOME_CURRENCY)

    def unit_matches_with(self, other):
        return (
            (isinstance(other, Money) and self._currency == other._currency)
            or
            (self.currency == getattr(other, "currency", None))
        )
