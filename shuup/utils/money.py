# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import decimal

from . import babel_precision_provider, numbers

DEFAULT_PRECISION = decimal.Decimal('0.01')


class Money(numbers.UnittedDecimal):
    """
    Money value with currency.

    The pure decimal value is available from the base classes
    `~shuup.utils.numbers.UnittedDecimal.value` property (preferred way)
    or by casting to `Decimal`.

    Money objects with different currencies cannot be compared or
    calculated with and will raise `~shuup.utils.numbers.UnitMixupError`.

    See `__new__`.
    """

    def __new__(cls, value="0", currency=None, *args, **kwargs):
        """
        Create new Money instance with given value and currency.

        If no currency is given explicitly and `value` has a property
        named `currency`, then that will be used.  Otherwise currency is
        a required argument and not passing one will raise a TypeError.

        :param str|numbers.Number value:
          Value as string or number
        :param str|None currency:
          Currency as ISO-4217 code (3-letter string) or None.
        """
        if currency is None and hasattr(value, 'currency'):
            currency = value.currency
        if not currency:
            raise TypeError('%s: currency must be given' % cls.__name__)
        instance = super(Money, cls).__new__(cls, value, *args, **kwargs)
        instance.currency = currency
        return instance

    def __repr__(self):
        cls_name = type(self).__name__
        return "%s('%s', %r)" % (cls_name, self.value, self.currency)

    def __reduce_ex__(self, protocol):
        return (type(self), (self.value, self.currency))

    def __str__(self):
        return "%s %s" % (self.value, self.currency)

    @classmethod
    def from_data(cls, value, currency):
        return cls(value, currency)

    def unit_matches_with(self, other):
        return (self.currency == getattr(other, 'currency', None))

    def new(self, value):
        return type(self)(value, currency=self.currency)

    def as_rounded(self, digits=None, rounding=decimal.ROUND_HALF_EVEN):
        """
        Get rounded value of self.

        Return the value rounded to given `digits` if specified,
        otherwise to the precision of ``self.currency`` as returned by
        the precision provider, see `set_precision_provider`.

        :type digits: int|None
        :param digits:  Number of digits to round to or None
        :type rounding: str
        :param rounding: Rounding mode to use

        :rtype: Money
        :return: A new `Money` instance with the rounded value
        """
        precision = _get_precision(self.currency, digits)
        return self.new(self.value.quantize(precision, rounding=rounding))


def set_precision_provider(precision_provider):
    """
    Set precision provider for Money instances.

    Default precision provider is
    `shuup.utils.babel_precision_provider.get_precision`.

    :type precision_provider: Callable[[str], decimal.Decimal|None]
    :param precision_provider:
      Function which will return precision for given currency code, or
      None for unhandled currency codes, e.g. ``func('USD')`` could
      return ``Decimal('0.01')``.
    """
    assert callable(precision_provider)
    global _precision_provider
    _precision_provider = precision_provider


_precision_provider = babel_precision_provider.get_precision


def _get_precision(currency, digits):
    if digits is None:
        return (_precision_provider(currency) or DEFAULT_PRECISION)
    precision = _digits_to_precision.get(digits)
    if precision is None:
        precision = decimal.Decimal('0.1') ** digits
        _digits_to_precision[digits] = precision
    return precision


_digits_to_precision = {2: decimal.Decimal('0.01')}
