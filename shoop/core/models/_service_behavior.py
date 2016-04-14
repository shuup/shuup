# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedField, TranslatedFields

from shoop.core.fields import MoneyValueField

from ._service_base import (
    ServiceBehaviorComponent, ServiceCost,
    TranslatableServiceBehaviorComponent
)


class FixedCostBehaviorComponent(TranslatableServiceBehaviorComponent):
    name = _("Fixed cost")
    help_text = _("Add fixed cost to price of the service.")

    price_value = MoneyValueField()
    description = TranslatedField(any_language=True)

    translations = TranslatedFields(
        description=models.CharField(max_length=100, blank=True, verbose_name=_("description")),
    )

    def get_costs(self, service, source):
        price = source.create_price(self.price_value)
        description = self.safe_translation_getter('description')
        yield ServiceCost(price, description)


class WaivingCostBehaviorComponent(TranslatableServiceBehaviorComponent):
    name = _("Waiving cost")
    help_text = _(
        "Add cost to price of the service if total price "
        "of products is less than a waive limit.")

    price_value = MoneyValueField()
    waive_limit_value = MoneyValueField()
    description = TranslatedField(any_language=True)

    translations = TranslatedFields(
        description=models.CharField(max_length=100, blank=True, verbose_name=_("description")),
    )

    def get_costs(self, service, source):
        waive_limit = source.create_price(self.waive_limit_value)
        product_total = source.total_price_of_products
        price = source.create_price(self.price_value)
        description = self.safe_translation_getter('description')
        zero_price = source.create_price(0)
        if product_total and product_total >= waive_limit:
            yield ServiceCost(zero_price, description, base_price=price)
        else:
            yield ServiceCost(price, description)


class WeightLimitsBehaviorComponent(ServiceBehaviorComponent):
    name = _("Weight limits")
    help_text = _(
        "Limit availability of the service based on "
        "total weight of products.")

    min_weight = models.DecimalField(
        max_digits=36, decimal_places=6, blank=True, null=True,
        verbose_name=_("minimum weight"))
    max_weight = models.DecimalField(
        max_digits=36, decimal_places=6, blank=True, null=True,
        verbose_name=_("maximum weight"))

    def get_unavailability_reasons(self, service, source):
        weight = sum(((x.get("weight") or 0) for x in source.get_lines()), 0)
        if self.min_weight:
            if weight < self.min_weight:
                yield ValidationError(_("Minimum weight not met."), code="min_weight")
        if self.max_weight:
            if weight > self.max_weight:
                yield ValidationError(_("Maximum weight exceeded."), code="max_weight")
