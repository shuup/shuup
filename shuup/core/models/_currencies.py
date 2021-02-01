# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import decimal

import babel
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinLengthValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from shuup.core import cache
from shuup.utils.analog import define_log_model


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
                                                      default=2,
                                                      help_text=_(
                                                          "The number of decimal places supported by this currency."))

    def clean(self):
        super(Currency, self).clean()

        # make sure the code is a valid ISO-4217 currency
        if self.code not in babel.Locale("en").currencies:
            raise ValidationError(_("Enter a valid ISO-4217 currency code."))

    def save(self, *args, **kwargs):
        super(Currency, self).save(*args, **kwargs)
        cache.bump_version('currency_precision')

    class Meta:
        verbose_name = _("currency")
        verbose_name_plural = _("currencies")

    def __str__(self):
        return self.code


def get_currency_precision(currency):
    """
    Get precision by currency code.

    Precision values will be populated from the ``decimal_places``
    fields of the `Currency` objects in the database.

    :type currency: str
    :param currency: Currency code as 3-letter string (ISO-4217).

    :rtype: decimal.Decimal|None
    :return: Precision value for a given currency code or None for unknown.
    """
    cache_key = 'currency_precision:' + currency
    precision = cache.get(cache_key)
    if precision is None:
        currency_obj = Currency.objects.filter(code=currency).first()
        precision = (
            decimal.Decimal('0.1') ** currency_obj.decimal_places
            if currency_obj else None)
        cache.set(cache_key, precision)
    return precision


CurrencyLogEntry = define_log_model(Currency)
