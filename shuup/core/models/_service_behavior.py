# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum
from parler.models import TranslatableModel, TranslatedField, TranslatedFields

from shuup.core.fields import MeasurementField, MoneyValueField

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


class WeightBasedPriceRange(TranslatableModel):
    component = models.ForeignKey(
        "WeightBasedPricingBehaviorComponent",
        related_name="ranges",
        on_delete=models.CASCADE
    )
    min_value = MeasurementField(unit="g", verbose_name=_("min weight"), blank=True, null=True)
    max_value = MeasurementField(unit="g", verbose_name=_("max weight"), blank=True, null=True)
    price_value = MoneyValueField()
    description = TranslatedField(any_language=True)

    translations = TranslatedFields(
        description=models.CharField(max_length=100, blank=True, verbose_name=_("description")),
    )

    def matches_to_value(self, value):
        return _is_in_range(value, self.min_value, self.max_value)


def _is_in_range(value, min_value, max_value):
    """
    Help function to check if the ``WeightBasedPriceRange`` matches

    If min_value is None the max_value determines if the range matches.
    None as a max_value represents infinity. Min value is counted in
    range only when it's zero. Max value is always part of the range.

    :type value: decimal.Decimal
    :type min_value: MeasurementField
    :type max_value: MeasurementField
    :rtype: bool
    """
    if value is None:
        return False
    if (not (min_value or max_value)) or (min_value == max_value == value):
        return True
    if (not min_value or value > min_value) and (max_value is None or value <= max_value):
        return True
    return False


class WeightBasedPricingBehaviorComponent(ServiceBehaviorComponent):
    name = _("Weight-based pricing")
    help_text = _(
        "Define price based on basket weight. "
        "Range minimums is counted in range only as zero.")

    def _get_matching_range_with_lowest_price(self, source):
        total_gross_weight = source.total_gross_weight
        matching_ranges = [range for range in self.ranges.all() if range.matches_to_value(total_gross_weight)]
        if not matching_ranges:
            return
        return min(matching_ranges, key=lambda x: x.price_value)

    def get_costs(self, service, source):
        range = self._get_matching_range_with_lowest_price(source)
        if range:
            price = source.create_price(range.price_value)
            description = range.safe_translation_getter('description')
            yield ServiceCost(price, description)

    def get_unavailability_reasons(self, service, source):
        range = self._get_matching_range_with_lowest_price(source)
        if not range:
            yield ValidationError(_("Weight does not match with any range."), code="out_of_range")


class GroupAvailabilityBehaviorComponent(ServiceBehaviorComponent):
    name = _("Contact group availability")
    help_text = _("Limit service availability for specific contact groups.")

    groups = models.ManyToManyField("ContactGroup", verbose_name=_("groups"))

    def get_unavailability_reasons(self, service, source):
        if source.customer and not source.customer.pk:
            yield ValidationError(_("Customer does not belong to any group."))
            return

        customer_groups = set(source.customer.groups.all().values_list("pk", flat=True))
        groups_to_match = set(self.groups.all().values_list("pk", flat=True))
        if not bool(customer_groups & groups_to_match):
            yield ValidationError(_("Service is not available for any of the customers groups."))


class StaffOnlyBehaviorComponent(ServiceBehaviorComponent):
    name = _("Staff only availability")
    help_text = _("Limit service availability to staff only")

    def get_unavailability_reasons(self, service, source):
        if not source.creator or not source.creator.is_staff:
            yield ValidationError(_("Service is only available for staff"))


class RoundingMode(Enum):
    ROUND_HALF_UP = decimal.ROUND_HALF_UP
    ROUND_HALF_DOWN = decimal.ROUND_HALF_DOWN
    ROUND_UP = decimal.ROUND_UP
    ROUND_DOWN = decimal.ROUND_DOWN

    class Labels:
        ROUND_HALF_UP = _("round to nearest with ties going away from zero")
        ROUND_HALF_DOWN = _("round to nearest with ties going towards zero")
        ROUND_UP = _("round away from zero")
        ROUND_DOWN = _("round towards zero")
