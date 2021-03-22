# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from shuup.core.models import Currency, get_currency_precision
from shuup.testing.factories import get_currency
from shuup.utils import money


@pytest.mark.django_db
def test_currency_validation():
    currency, _ = Currency.objects.get_or_create(code="USD")
    currency.full_clean()
    assert "USD" in str(currency)

    # currency code does not exist
    with pytest.raises(ValidationError) as exc:
        Currency(code="ISD").full_clean()

    assert "Enter a valid ISO-4217 currency code." in exc.value.messages


@pytest.mark.django_db
def test_currency_precision_provider_basics():
    get_currency("USD", 2)
    get_currency("EUR", 2)
    get_currency("JPY", 0)
    assert get_currency_precision("USD") == Decimal("0.01")
    assert get_currency_precision("EUR") == Decimal("0.01")
    assert get_currency_precision("JPY") == Decimal("1")


@pytest.mark.django_db
def test_currency_precision_provider_non_existing():
    assert get_currency_precision("XPT") is None


@pytest.mark.django_db
def test_currency_precision_provider_override():
    currency_usd = get_currency("USD")
    currency_usd.decimal_places = 6
    currency_usd.save()
    assert get_currency_precision("USD") == Decimal("0.000001")
    assert currency_usd.decimal_places == 6

    # change it and check if the precision provider has updated
    currency_usd.decimal_places = 2
    currency_usd.save()
    assert get_currency_precision("USD") == Decimal("0.01")


def test_currency_precision_provider_is_acceptable():
    money.set_precision_provider(get_currency_precision)
