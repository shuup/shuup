# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from decimal import Decimal

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField
from shoop.utils.numbers import bankers_round, parse_decimal_string

__all__ = ("SalesUnit",)


@python_2_unicode_compatible
class SalesUnit(TranslatableModel):
    identifier = InternalIdentifierField(unique=True)
    decimals = models.PositiveSmallIntegerField(default=0, verbose_name=_(u"allowed decimals"))

    translations = TranslatedFields(
        name=models.CharField(max_length=128, verbose_name=_('name')),
        short_name=models.CharField(max_length=128, verbose_name=_('short name')),
    )

    class Meta:
        verbose_name = _('sales unit')
        verbose_name_plural = _('sales units')

    def __str__(self):
        return str(self.safe_translation_getter("name", default=None))

    @property
    def allow_fractions(self):
        return self.decimals > 0

    @cached_property
    def quantity_step(self):
        """
        Get the quantity increment for the amount of decimals this unit allows.

        For 0 decimals, this will be 1; for 1 decimal, 0.1; etc.

        :return: Decimal in (0..1]
        :rtype: Decimal
        """

        # This particular syntax (`10 ^ -n`) is the same that `bankers_round` uses
        # to figure out the quantizer.

        return Decimal(10) ** (-int(self.decimals))

    def round(self, value):
        return bankers_round(parse_decimal_string(value), self.decimals)
