# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from filer.fields.image import FilerImageField
from jsonfield import JSONField
from parler.models import TranslatedFields

from shoop.core.fields import CurrencyField, InternalIdentifierField
from shoop.core.pricing import TaxfulPrice, TaxlessPrice

from ._base import ChangeProtected, TranslatableShoopModel
from ._orders import Order


def _get_default_currency():
    return settings.SHOOP_HOME_CURRENCY


class ShopStatus(Enum):
    DISABLED = 0
    ENABLED = 1


@python_2_unicode_compatible
class Shop(ChangeProtected, TranslatableShoopModel):
    protected_fields = ["currency", "prices_include_tax"]
    change_protect_message = _("The following fields cannot be changed since there are existing orders for this shop")

    identifier = InternalIdentifierField(unique=True)
    domain = models.CharField(max_length=128, blank=True, null=True, unique=True)
    status = EnumIntegerField(ShopStatus, default=ShopStatus.DISABLED)
    owner = models.ForeignKey("Contact", blank=True, null=True, on_delete=models.SET_NULL)
    options = JSONField(blank=True, null=True)
    currency = CurrencyField(default=_get_default_currency)
    prices_include_tax = models.BooleanField(default=True)
    logo = FilerImageField(verbose_name=_("logo"), blank=True, null=True, on_delete=models.SET_NULL)
    maintenance_mode = models.BooleanField(verbose_name=_("maintenance mode"), default=False)

    translations = TranslatedFields(
        name=models.CharField(max_length=64),
        public_name=models.CharField(max_length=64),
        maintenance_message=models.CharField(max_length=300, blank=True)
    )

    def __str__(self):
        return self.safe_translation_getter("name", default="Shop %d" % self.pk)

    def create_price(self, value):
        """
        Create a price with given value and settings of this shop.

        Takes the ``prices_include_tax`` and ``currency`` settings of
        this Shop into account.

        :type value: decimal.Decimal|int|str
        :rtype: shoop.core.pricing.Price
        """
        if self.prices_include_tax:
            return TaxfulPrice(value, self.currency)
        else:
            return TaxlessPrice(value, self.currency)

    def _are_changes_protected(self):
        return Order.objects.filter(shop=self).exists()
