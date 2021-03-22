# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal


class UnittedDecimal(decimal.Decimal):
    """
    Decimal with unit.

    Allows creating decimal classes that cannot be mixed, e.g. to
    prevent operations like::

        TaxfulPrice(1) + TaxlessPrice(2)

    where `TaxfulPrice` and `TaxlessPrice` are subclasses of
    `UnittedDecimal`.
    """

    @property
    def value(self):
        """
        Value of this decimal without the unit.

        :rtype: decimal.Decimal
        """
        return decimal.Decimal(self)

    def __repr__(self):
        decimal_repr = super(UnittedDecimal, self).__repr__()
        return decimal_repr.replace("Decimal", type(self).__name__)

    def unit_matches_with(self, other):
        """
        Test if self and other have matching units.

        :rtype: bool
        """
        raise NotImplementedError("Error! Not implemented: `UnittedDecimal` -> `unit_matches_with()`.")

    def new(self, value):
        """
        Create new instance with given value using same unit as self.

        Post-condition: If ``x = y.new(v)``, then
        ``x.unit_matches_with(y) and x.value == v``.

        :type value:
        :return: Object with same type as self and matching unit, but with given decimal value.
        :rtype: UnittedDecimal
        """
        return type(self)(value)

    def _check_units_match(self, other):
        if not self.unit_matches_with(other):
            raise UnitMixupError(self, other)

    def __lt__(self, other, **kwargs):
        self._check_units_match(other)
        return super(UnittedDecimal, self).__lt__(other, **kwargs)

    def __le__(self, other, **kwargs):
        self._check_units_match(other)
        return super(UnittedDecimal, self).__le__(other, **kwargs)

    def __gt__(self, other, **kwargs):
        self._check_units_match(other)
        return super(UnittedDecimal, self).__gt__(other, **kwargs)

    def __ge__(self, other, **kwargs):
        self._check_units_match(other)
        return super(UnittedDecimal, self).__ge__(other, **kwargs)

    def __eq__(self, other, *args, **kwargs):
        if not self.unit_matches_with(other):
            return False
        return super(UnittedDecimal, self).__eq__(other, **kwargs)

    def __ne__(self, other, *args, **kwargs):
        if not self.unit_matches_with(other):
            return True
        return super(UnittedDecimal, self).__ne__(other, **kwargs)

    def __add__(self, other, **kwargs):
        self._check_units_match(other)
        return self.new(super(UnittedDecimal, self).__add__(other, **kwargs))

    def __sub__(self, other, **kwargs):
        self._check_units_match(other)
        return self.new(super(UnittedDecimal, self).__sub__(other, **kwargs))

    def __mul__(self, other, **kwargs):
        if isinstance(other, UnittedDecimal):
            raise TypeError("Error! Cannot multiply %r with %r." % (self, other))
        return self.new(super(UnittedDecimal, self).__mul__(other, **kwargs))

    def __radd__(self, other, **kwargs):
        return self.__add__(other, **kwargs)

    def __rsub__(self, other, **kwargs):
        return (-self).__add__(other, **kwargs)

    def __rmul__(self, other, **kwargs):
        return self.__mul__(other, **kwargs)

    def __truediv__(self, other, **kwargs):
        if isinstance(other, UnittedDecimal):
            self._check_units_match(other)
            return super(UnittedDecimal, self).__truediv__(other, **kwargs)
        else:
            value = super(UnittedDecimal, self).__truediv__(other, **kwargs)
            return self.new(value)

    def __rtruediv__(self, other, **kwargs):
        if not isinstance(other, UnittedDecimal):
            type_name = type(self).__name__
            raise TypeError("Error! Cannot divide non-{0} with {0}.".format(type_name))
        self._check_units_match(other)
        return super(UnittedDecimal, self).__rtruediv__(other, **kwargs)

    __div__ = __truediv__
    __rdiv__ = __rtruediv__

    def __floordiv__(self, other, **kwargs):
        if not isinstance(other, UnittedDecimal):
            type_name = type(self).__name__
            msg = "Error! Cannot floor-div {0} with non-{0}.".format(type_name)
            raise TypeError(msg)
        self._check_units_match(other)
        return super(UnittedDecimal, self).__floordiv__(other, **kwargs)

    def __rfloordiv__(self, other, **kwargs):
        if not isinstance(other, UnittedDecimal):
            type_name = type(self).__name__
            msg = "Error! Cannot floor-div non-{0} with {0}.".format(type_name)
            raise TypeError(msg)
        self._check_units_match(other)
        return super(UnittedDecimal, self).__rfloordiv__(other, **kwargs)

    def __mod__(self, other, **kwargs):
        if not isinstance(other, UnittedDecimal):
            type_name = type(self).__name__
            raise TypeError("Error! Cannot modulo {0} with non-{0}.".format(type_name))
        self._check_units_match(other)
        return self.new(super(UnittedDecimal, self).__mod__(other, **kwargs))

    def __divmod__(self, other, **kwargs):
        if not isinstance(other, UnittedDecimal):
            type_name = type(self).__name__
            raise TypeError("Error! Cannot divmod {0} with non-{0}.".format(type_name))
        self._check_units_match(other)
        (div, mod) = super(UnittedDecimal, self).__divmod__(other, **kwargs)
        return (div, self.new(mod))

    def __pow__(self, other, **kwargs):
        type_name = type(self).__name__
        raise TypeError("Error! {} cannot be powered.".format(type_name))

    def __neg__(self, **kwargs):
        return self.new(super(UnittedDecimal, self).__neg__(**kwargs))

    def __pos__(self, **kwargs):
        return self.new(super(UnittedDecimal, self).__pos__(**kwargs))

    def __abs__(self, **kwargs):
        return self.new(super(UnittedDecimal, self).__abs__(**kwargs))

    def __int__(self, **kwargs):
        return super(UnittedDecimal, self).__int__(**kwargs)

    def __float__(self, **kwargs):
        return super(UnittedDecimal, self).__float__(**kwargs)

    def __round__(self, ndigits=0, **kwargs):
        value = super(UnittedDecimal, self).__round__(ndigits, **kwargs)
        return self.new(value)

    def quantize(self, exp, *args, **kwargs):
        value = super(UnittedDecimal, self).quantize(exp, *args, **kwargs)
        return self.new(value)

    def copy_negate(self, *args, **kwargs):
        value = super(UnittedDecimal, self).copy_negate(*args, **kwargs)
        return self.new(value)


class UnitMixupError(TypeError):
    """
    Invoked operation for UnittedDecimal and object with non-matching unit.

    The objects involved are stored in instance variables `obj1` and
    `obj2`.  Former is instance of :class:`UnittedDecimal` or its
    subclass and the other could be any object.

    :ivar UnittedDecimal obj1: Involved object 1.
    :ivar Any obj2: Involved object 2.
    """

    def __init__(self, obj1, obj2, msg="Unit mixup"):
        self.obj1 = obj1
        self.obj2 = obj2
        super(UnitMixupError, self).__init__(msg)

    def __str__(self):
        super_str = super(UnitMixupError, self).__str__()
        return "%s: %r vs %r" % (super_str, self.obj1, self.obj2)
