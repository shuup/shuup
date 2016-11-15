# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import decimal
from decimal import ROUND_HALF_EVEN

from babel.core import get_global

from . import numbers

# map of precisions for currencies
CURRENCY_PRECISIONS = {}

# map of precisions for digits
DIGITS_PRECISIONS = {}

# the precision provider function
_precision_provider_func = None


def make_precision(digits):
    """ Return a precision for a given number of digits """
    return decimal.Decimal('0.1') ** digits


def get_babel_digits(currency):
    """ Get the number of digits used by the currency from Babel """
    fractions = get_global('currency_fractions')
    try:
        return fractions[currency][0]
    except KeyError:
        return fractions['DEFAULT'][0]


def get_precision(digits=None, currency=None):
    """
    Returns the precision for the given digits or currency.
    digits is required argument if no currency is passed

    babel will be used to fetch the number of digits of the currency

    :param int|None digits:
      Number of digits to use for precision

    :param str|None currency:
      Currency as ISO-4217 code (3-letter string) or None.
    """
    assert (digits is not None or currency is not None)

    if digits is None:
        if currency not in CURRENCY_PRECISIONS:
            CURRENCY_PRECISIONS[currency] = make_precision(get_babel_digits(currency))

        return CURRENCY_PRECISIONS[currency]
    else:
        if digits not in DIGITS_PRECISIONS:
            DIGITS_PRECISIONS[digits] = make_precision(digits)

        return DIGITS_PRECISIONS[digits]


def set_precision_provider_function(precision_provider_func):
    """
    Set the precision provider function to be used by Money when rounding

    :param precision_provider_func function(digits, currency):
      the function which will return the precision for the given arguments
    """
    assert callable(precision_provider_func)
    global _precision_provider_func
    _precision_provider_func = precision_provider_func


# sets the default precision provider function
set_precision_provider_function(get_precision)


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

    def as_rounded(self, digits=None, rounding=ROUND_HALF_EVEN):
        """
        Returns the value rounded to the given `digits` if specified,
        otherwise through the currency of the this instance.

        The precision will be fetched from the `precision_provider_func`.

        :param digits int:
          The number of digits to round
        :type rounding: str

        :return A new value rounded to the given digits or currency
        """

        precision = _precision_provider_func(digits, self.currency)
        return self.new(self.value.quantize(precision, rounding=rounding))
