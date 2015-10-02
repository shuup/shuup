# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields

from shoop.core.fields import CurrencyField, InternalIdentifierField, MoneyValueField
from shoop.utils.i18n import format_money, format_percent
from shoop.utils.properties import MoneyProperty, MoneyPropped

from ._base import ImmutableMixin, TranslatableShoopModel


class Tax(MoneyPropped, ImmutableMixin, TranslatableShoopModel):
    identifier_attr = 'code'

    immutability_message = _(
        "Cannot change business critical fields of Tax that is in use")
    unprotected_fields = ['enabled']

    code = InternalIdentifierField(unique=True)

    translations = TranslatedFields(
        name=models.CharField(max_length=64),
    )

    rate = models.DecimalField(
        max_digits=6, decimal_places=5, blank=True, null=True,
        verbose_name=_('tax rate'),
        help_text=_("The percentage rate of the tax. Mutually exclusive with flat amounts.")
    )
    amount = MoneyProperty('amount_value', 'currency')
    amount_value = MoneyValueField(
        default=None, blank=True, null=True,
        verbose_name=_('tax amount'),
        help_text=_("The flat amount of the tax. Mutually exclusive with percentage rates.")
    )
    currency = CurrencyField(default=None, blank=True, null=True)
    enabled = models.BooleanField(default=True, verbose_name=_('enabled'))

    def clean(self):
        super(Tax, self).clean()
        if self.rate is None and self.amount is None:
            raise ValidationError(_('Either rate or amount is required'))
        if self.amount is not None and self.rate is not None:
            raise ValidationError(_('Cannot have both rate and amount'))
        if self.amount is not None and not self.currency:
            raise ValidationError(
                _("Currency is required if amount is specified"))

    def calculate_amount(self, base_amount):
        """
        Calculate tax amount with this tax for given base amount.

        :type base_amount: shoop.utils.money.Money
        :rtype: shoop.utils.money.Money
        """
        if self.amount is not None:
            return self.amount
        if self.rate is not None:
            return self.rate * base_amount
        raise ValueError("Improperly configured tax: %s" % self)

    def __str__(self):
        text = super(Tax, self).__str__()
        if self.rate is not None:
            text += " ({})".format(format_percent(self.rate, digits=3))
        if self.amount is not None:
            text += " ({})".format(format_money(self.amount))
        return text

    def _is_in_use(self):
        return self.order_line_taxes.exists()

    class Meta:
        verbose_name = _('tax')
        verbose_name_plural = _('taxes')


class TaxClass(TranslatableShoopModel):
    identifier = InternalIdentifierField(unique=True)
    translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_('name')),
    )
    enabled = models.BooleanField(default=True, verbose_name=_('enabled'))

    class Meta:
        verbose_name = _('tax class')
        verbose_name_plural = _('tax classes')


class CustomerTaxGroup(TranslatableShoopModel):
    identifier = InternalIdentifierField(unique=True)
    translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_('name')),
    )
    enabled = models.BooleanField(default=True, verbose_name=_('enabled'))

    class Meta:
        verbose_name = _('customer tax group')
        verbose_name_plural = _('customer tax groups')
