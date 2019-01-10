# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields

from shuup.core.fields import (
    CurrencyField, InternalIdentifierField, MoneyValueField
)
from shuup.utils.analog import define_log_model
from shuup.utils.i18n import format_money, format_percent
from shuup.utils.properties import MoneyProperty, MoneyPropped

from ._base import ChangeProtected, TranslatableShuupModel


class Tax(MoneyPropped, ChangeProtected, TranslatableShuupModel):
    identifier_attr = 'code'

    change_protect_message = _(
        "Cannot change business critical fields of Tax that is in use")
    unprotected_fields = ['enabled']

    code = InternalIdentifierField(
        unique=True, editable=True, verbose_name=_("code"), help_text=_("The abbreviated tax code name."))

    translations = TranslatedFields(
        name=models.CharField(max_length=124, verbose_name=_("name"), help_text=_(
                "The tax name. This is shown in order lines in order invoices and confirmations."
            )
        ),
    )

    rate = models.DecimalField(
        max_digits=6, decimal_places=5, blank=True, null=True,
        verbose_name=_("tax rate"), help_text=_(
            "The percentage rate of the tax."))
    amount = MoneyProperty('amount_value', 'currency')
    amount_value = MoneyValueField(
        default=None, blank=True, null=True,
        verbose_name=_("tax amount value"), help_text=_(
            "The flat amount of the tax. "
            "Mutually exclusive with percentage rates."))
    currency = CurrencyField(
        default=None, blank=True, null=True,
        verbose_name=_("currency of tax amount"))

    enabled = models.BooleanField(default=True, verbose_name=_('enabled'), help_text=_(
        "Check this if this tax is valid and active."
    ))

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

        :type base_amount: shuup.utils.money.Money
        :rtype: shuup.utils.money.Money
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

    def _are_changes_protected(self):
        return self.order_line_taxes.exists()

    class Meta:
        verbose_name = _('tax')
        verbose_name_plural = _('taxes')


class TaxClass(TranslatableShuupModel):
    identifier = InternalIdentifierField(unique=True)
    translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_('name'), help_text=_(
                "The tax class name. "
                "Tax classes are used to control how taxes are applied to products."
            )
        ),
    )
    enabled = models.BooleanField(default=True, verbose_name=_('enabled'), help_text=_(
        "Check this if this tax class is active and valid."
    ))

    class Meta:
        verbose_name = _('tax class')
        verbose_name_plural = _('tax classes')


class CustomerTaxGroup(TranslatableShuupModel):
    identifier = InternalIdentifierField(unique=True)
    translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_('name'), help_text=_(
                "The customer tax group name. "
                "Customer tax groups can be used to control how taxes are applied to a set of customers. "
            )
        ),
    )
    enabled = models.BooleanField(default=True, verbose_name=_('enabled'))

    class Meta:
        verbose_name = _('customer tax group')
        verbose_name_plural = _('customer tax groups')

    @classmethod
    def get_default_person_group(cls):
        obj, c = CustomerTaxGroup.objects.get_or_create(identifier="default_person_customers", defaults={
            "name": _("Retail Customers")
        })
        return obj

    @classmethod
    def get_default_company_group(cls):
        obj, c = CustomerTaxGroup.objects.get_or_create(identifier="default_company_customers", defaults={
            "name": _("Company Customers")
        })
        return obj


TaxLogEntry = define_log_model(Tax)
TaxClassLogEntry = define_log_model(TaxClass)
CustomerTaxGroupLogEntry = define_log_model(CustomerTaxGroup)
