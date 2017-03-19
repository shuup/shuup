# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

import warnings
from decimal import Decimal

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedField, TranslatedFieldsModel

from shuup.core.fields import InternalIdentifierField
from shuup.utils.numbers import bankers_round, parse_decimal_string

from ._base import TranslatableShuupModel


# TODO: (2.0) Remove deprecated SalesUnit.short_name
class _ShortNameToSymbol(object):
    def __init__(self, *args, **kwargs):
        if 'short_name' in kwargs:
            self._issue_deprecation_warning()
            kwargs.setdefault('symbol', kwargs.pop('short_name'))
        super(_ShortNameToSymbol, self).__init__(*args, **kwargs)

    @property
    def short_name(self):
        self._issue_deprecation_warning()
        return self.symbol

    @short_name.setter
    def short_name(self, value):
        self._issue_deprecation_warning()
        self.symbol = value

    def _issue_deprecation_warning(self):
        warnings.warn(
            "short_name is deprecated, use symbol instead", DeprecationWarning)


@python_2_unicode_compatible
class SalesUnit(_ShortNameToSymbol, TranslatableShuupModel):
    identifier = InternalIdentifierField(unique=True)
    decimals = models.PositiveSmallIntegerField(default=0, verbose_name=_(u"allowed decimal places"), help_text=_(
        "The number of decimal places allowed by this sales unit."
        "Set this to a value greater than zero if products with this sales unit can be sold in fractional quantities"
    ))

    name = TranslatedField()
    symbol = TranslatedField()

    class Meta:
        verbose_name = _('sales unit')
        verbose_name_plural = _('sales units')

    def __str__(self):
        return self.safe_translation_getter("name", default=self.identifier) or ""

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


class SalesUnitTranslation(_ShortNameToSymbol, TranslatedFieldsModel):
    master = models.ForeignKey(
        SalesUnit, related_name='translations', null=True, editable=False)
    name = models.CharField(
        max_length=128, verbose_name=_('name'), help_text=_(
            "The sales unit name to use for products (For example, "
            "'pieces' or 'units'). Sales units can be set for each "
            "product through the product editor view."))
    symbol = models.CharField(
        max_length=128, verbose_name=_("symbol"), help_text=_(
            "An abbreviated name for this sales unit that is shown "
            "throughout admin and order invoices."))

    class Meta:
        # Use same meta options as Parler's defaults to avoid migration
        unique_together = [('language_code', 'master')]
        verbose_name = "sales unit Translation"
        db_table = SalesUnit._meta.db_table + '_translation'
        db_tablespace = SalesUnit._meta.db_tablespace
        managed = SalesUnit._meta.managed
        default_permissions = ()
