# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import babel
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinLengthValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from shuup.utils.analog import define_log_model
from shuup.utils.money import get_precision as money_get_precision
from shuup.utils.money import make_precision

# map of precisions for currencies
CURRENCY_PRECISIONS = {}


@python_2_unicode_compatible
class Currency(models.Model):
    identifier_attr = 'code'

    code = models.CharField(verbose_name=_("code"),
                            max_length=3, unique=True,
                            editable=True,
                            validators=[MinLengthValidator(3)],
                            help_text=_("The ISO-4217 code of the currency"))

    decimal_places = models.PositiveSmallIntegerField(verbose_name=_("decimal places"),
                                                      validators=[MaxValueValidator(10)],
                                                      default=2)

    def clean(self):
        super(Currency, self).clean()

        # make sure the code is a valid ISO-4217 currency
        if self.code not in babel.Locale("en").currency_symbols:
            raise ValidationError(_('Enter a valid ISO-4217 currency code'))

    class Meta:
        verbose_name = _("currency")
        verbose_name_plural = _("currencies")

    def __str__(self):
        return self.code


def override_currency_precision(currency, precision):
    """
    Overrides the precision for the given currency in the module internal map.

    :param str currency:
      Currency as ISO-4217 code (3-letter string).
    :param decimal.Decimal precision:
      The currency precision
    """
    CURRENCY_PRECISIONS[currency] = precision


def get_currency_precision(digits=None, currency=None):
    """
    Returns the precision for the given digits or currency.
    digits is required argument if no currency is passed

    Currency model will be used to fetch the number of digits of the currency

    :param int|None digits:
      Number of digits to use for precision

    :param str|None currency:
      Currency as ISO-4217 code (3-letter string) or None.
    """
    assert (digits is not None or currency is not None)

    if digits is None:
        if currency not in CURRENCY_PRECISIONS:
            try:
                digits = Currency.objects.get(code=currency).decimal_places
                override_currency_precision(currency, make_precision(digits))
            except Currency.DoesNotExist:
                override_currency_precision(currency, money_get_precision(currency=currency))

        return CURRENCY_PRECISIONS[currency]
    else:
        return money_get_precision(digits=digits)


CurrencyLogEntry = define_log_model(Currency)
