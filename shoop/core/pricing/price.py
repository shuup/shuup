# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import decimal

from shoop.utils.money import Money


class Price(Money):
    includes_tax = None

    def __new__(cls, value="0", *args, **kwargs):
        if cls == Price:
            raise TypeError('Do not create direct instances of Price')
        return super(Price, cls).__new__(cls, value, *args, **kwargs)

    def _units_match(self, other):
        if not super(Price, self)._units_match(other):
            return False
        self_includes_tax = getattr(self, 'includes_tax', None)
        other_includes_tax = getattr(other, 'includes_tax', None)
        return (self_includes_tax == other_includes_tax)

    @property
    def amount(self):
        return decimal.Decimal(self)

    @classmethod
    def from_value(cls, value, includes_tax):
        if includes_tax:
            return TaxfulPrice(value)
        else:
            return TaxlessPrice(value)


class TaxfulPrice(Price):
    includes_tax = True


class TaxlessPrice(Price):
    includes_tax = False
