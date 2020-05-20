# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.utils.money import Money


class Price(Money):
    """
    Money amount with taxful/taxless info.

    Taxful and taxless prices cannot be mixed in comparison or in
    calculations, i.e. operations like ``x < y`` or ``x + y`` for two
    Prices ``x`` and ``y`` with ``x.includes_tax != y.includes_tax``
    will raise an :obj:`~shuup.utils.numbers.UnitMixupError`.

    In addition to `includes_tax` info, Prices are Money and know their
    `~shuup.utils.numbers.UnittedDecimal.value` and
    `~shuup.utils.money.Money.currency`.  To get the bare Money amount
    of a `Price`, use the `amount` property.
    """
    includes_tax = None

    def __new__(cls, value="0", *args, **kwargs):
        if cls == Price:
            raise TypeError('Error! Do not create direct instances of Price.')
        return super(Price, cls).__new__(cls, value, *args, **kwargs)

    def unit_matches_with(self, other):
        if not super(Price, self).unit_matches_with(other):
            return False
        self_includes_tax = getattr(self, 'includes_tax', None)
        other_includes_tax = getattr(other, 'includes_tax', None)
        return (self_includes_tax == other_includes_tax)

    @property
    def amount(self):
        """
        Money amount of this price.

        :rtype: Money
        """
        return Money(self.value, self.currency)

    @classmethod
    def from_data(cls, value, currency, includes_tax=None):
        if includes_tax is None:
            if cls.includes_tax is None:
                msg = 'Error! Missing includes_tax argument for %s.from_data.'
                raise TypeError(msg % (cls.__name__,))
            includes_tax = cls.includes_tax
        if includes_tax:
            return TaxfulPrice(value, currency)
        else:
            return TaxlessPrice(value, currency)

    def __str__(self):
        incl = 'incl.' if self.includes_tax else 'excl.'
        return '%s (%s tax)' % (super(Price, self).__str__(), incl)


class TaxfulPrice(Price):
    """
    Price which includes taxes.

    Check the base class, :obj:`Price`,  for more info.
    """
    includes_tax = True


class TaxlessPrice(Price):
    """
    Price which does not include taxes.

    Check the base class, :obj:`Price`,  for more info.
    """
    includes_tax = False
