# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError

from shuup.testing.factories import get_currency

import shuup.core.models._currencies as currencies_module
from shuup.core.models._currencies import Currency, get_currency_precision
from shuup.utils.money import get_babel_digits, make_precision, set_precision_provider_function


@pytest.mark.django_db
def test_currency_validation():
    currency = Currency(code="USD")
    currency.full_clean()
    assert "USD" in str(currency)

    # currency code does not exist
    with pytest.raises(ValidationError) as exc:
        Currency(code="ISD").full_clean()

    assert "Enter a valid ISO-4217 currency code" in exc.value.messages


@pytest.mark.django_db
def test_currency_precision_provider():
    # currencies clear
    currencies_module.CURRENCY_PRECISIONS.clear()

    # get precision from digits
    assert get_currency_precision(digits=0) == make_precision(0)
    assert get_currency_precision(digits=1) == make_precision(1)
    assert get_currency_precision(digits=2) == make_precision(2)
    assert get_currency_precision(digits=3) == make_precision(3)
    assert get_currency_precision(digits=4) == make_precision(4)

    # get precisions from currency
    assert get_currency_precision(currency="USD") == make_precision(get_babel_digits("USD"))
    assert get_currency_precision(currency="EUR") == make_precision(get_babel_digits("EUR"))
    assert get_currency_precision(currency="JPY") == make_precision(get_babel_digits("JPY"))

    # precisions are loaded
    assert sorted(currencies_module.CURRENCY_PRECISIONS.keys()) == sorted(["USD", "EUR", "JPY"])

    # force clear precisions
    currencies_module.CURRENCY_PRECISIONS.clear()

    # override a currency
    currency_usd = get_currency("USD", 6)
    assert get_currency_precision(currency="USD") == make_precision(6)

    # currency not found, the Babel default is 2
    assert get_currency_precision(currency="XPT") == make_precision(2)

    # acceptable function
    set_precision_provider_function(get_currency_precision)

    # check the values before the signal executes
    assert currency_usd.decimal_places == 6
    assert currencies_module.CURRENCY_PRECISIONS[currency_usd.code] == make_precision(6)

    # change it and check if the signal was able to change its value
    currency_usd.decimal_places = 4
    currency_usd.save()
    assert currencies_module.CURRENCY_PRECISIONS[currency_usd.code] == make_precision(4)
