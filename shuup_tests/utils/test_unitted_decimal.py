# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
import six
from decimal import Decimal

from shuup.utils.numbers import UnittedDecimal


class BaseDecimal(UnittedDecimal):
    unit = None

    def unit_matches_with(self, other):
        return self.unit == getattr(other, "unit", None)


class FooDecimal(BaseDecimal):
    unit = "foo"


class BarDecimal(BaseDecimal):
    unit = "bar"


def test_unitted_decimal_basics():
    assert FooDecimal(1) + FooDecimal(2) == FooDecimal(3)
    assert FooDecimal(3) - FooDecimal(2) == FooDecimal(1)
    assert FooDecimal(1) < FooDecimal(2)
    assert FooDecimal(2) * 5 == FooDecimal(10)
    assert 5 * FooDecimal(2) == FooDecimal(10)
    assert FooDecimal(7) / FooDecimal(2) == Decimal("3.5")
    assert FooDecimal(7) // FooDecimal(2) == 3
    assert FooDecimal(7) / 2 == FooDecimal("3.5")
    assert -FooDecimal(4) == FooDecimal("-4")


def test_unitted_decimal_value():
    assert FooDecimal(42).value == 42
    assert type(FooDecimal(42).value) == Decimal


def test_unit_mixups():
    with pytest.raises(TypeError):
        FooDecimal(1) + BarDecimal(2)
    with pytest.raises(TypeError):
        FooDecimal(1) + 2
    with pytest.raises(TypeError):
        1 + FooDecimal(1)
    with pytest.raises(TypeError):
        FooDecimal(1) - 2
    with pytest.raises(TypeError):
        2 - FooDecimal(1)
    with pytest.raises(TypeError):
        1 / FooDecimal(2)
    with pytest.raises(TypeError):
        1 // FooDecimal(2)


def test_equality():
    assert FooDecimal(1) == FooDecimal(1)
    assert FooDecimal(1) != FooDecimal(2)
    assert FooDecimal(1) != 1
    assert FooDecimal(1) != BarDecimal(1)
    assert not (FooDecimal(1) == BarDecimal(1))


def test_comparison():
    assert FooDecimal(1) < FooDecimal(2)
    assert FooDecimal(1) <= FooDecimal(2)
    assert FooDecimal(1) <= FooDecimal(1)
    assert FooDecimal(2) > FooDecimal(1)
    assert FooDecimal(2) >= FooDecimal(1)
    assert FooDecimal(2) >= FooDecimal(2)


def test_comparison_unit_mixups():
    with pytest.raises(TypeError):
        FooDecimal(1) < BarDecimal(2)
    with pytest.raises(TypeError):
        FooDecimal(1) <= BarDecimal(2)
    with pytest.raises(TypeError):
        FooDecimal(1) <= BarDecimal(1)
    with pytest.raises(TypeError):
        FooDecimal(2) > BarDecimal(1)
    with pytest.raises(TypeError):
        FooDecimal(2) >= BarDecimal(1)
    with pytest.raises(TypeError):
        FooDecimal(2) >= BarDecimal(2)


def test_mixing_with_zero():
    with pytest.raises(TypeError):
        FooDecimal(3) + 0
    with pytest.raises(TypeError):
        FooDecimal(3) - 0


def test_invalid_multiplication():
    with pytest.raises(TypeError):
        FooDecimal(2) * FooDecimal(3)


def test_invalid_power():
    with pytest.raises(TypeError):
        FooDecimal(2) ** 4
    with pytest.raises(TypeError):
        FooDecimal(2) ** FooDecimal(4)


def test_base_class_units_match_unimplemented():
    with pytest.raises(NotImplementedError):
        UnittedDecimal().unit_matches_with(UnittedDecimal())


def test_floordiv():
    assert FooDecimal(8) // FooDecimal(3) == 2
    with pytest.raises(TypeError):
        FooDecimal(8) // 3


def test_rdivs():
    class OtherFooDecimal(FooDecimal):
        def __rtruediv__(self, other, **kwargs):
            return super(OtherFooDecimal, self).__rtruediv__(other, **kwargs)

        __rdiv__ = __rtruediv__

        def __rfloordiv__(self, other, **kwargs):
            return super(OtherFooDecimal, self).__rfloordiv__(other, **kwargs)

    assert FooDecimal(12) / OtherFooDecimal(3) == 4
    assert FooDecimal(13) // OtherFooDecimal(3) == 4


def test_mod():
    assert FooDecimal(11) % FooDecimal(7) == FooDecimal(4)
    with pytest.raises(TypeError):
        FooDecimal(11) % 7


def test_divmod():
    FD = FooDecimal
    assert divmod(FD(11), FD(7)) == (1, FD(4))
    with pytest.raises(TypeError):
        divmod(FooDecimal(11), 7)


def test_pos():
    assert +FooDecimal(3) == FooDecimal(3)


def test_abs():
    assert abs(FooDecimal("-2")) == FooDecimal(2)


def test_int():
    assert int(FooDecimal(42)) == 42


def test_float():
    assert float(FooDecimal("42.5")) == 42.5


def test_round():
    if six.PY2:
        # Python 2 does not have __round__ operator
        with pytest.raises(AttributeError):
            FooDecimal("42.46").__round__()
        assert round(FooDecimal("42.46")) == 42
        assert round(FooDecimal("42.46"), 1) == 42.5
    else:
        assert round(FooDecimal("42.46")) == FooDecimal(42)
        assert round(FooDecimal("42.46"), 1) == FooDecimal("42.5")


def test_quantize():
    assert FooDecimal("42.66").quantize(Decimal("0.1")) == FooDecimal("42.7")


def test_copy_negate():
    assert FooDecimal(1).copy_negate() == FooDecimal(-1)


def test_unit_mixup_error_message():
    error = None
    try:
        FooDecimal(1) + BarDecimal(1)
    except TypeError as e:
        error = e
    assert str(error) == "Unit mixup: FooDecimal('1') vs BarDecimal('1')"
