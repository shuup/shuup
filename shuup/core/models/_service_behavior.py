# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

import decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum
from jsonfield import JSONField
from parler.models import TranslatableModel, TranslatedField, TranslatedFields

from shuup.core.fields import MeasurementField, MoneyValueField

from ._addresses import REGION_ISO3166
from ._service_base import ServiceBehaviorComponent, ServiceCost, TranslatableServiceBehaviorComponent


class FixedCostBehaviorComponent(TranslatableServiceBehaviorComponent):
    name = _("Fixed cost")
    help_text = _("Add a fixed cost to the price of the service.")

    price_value = MoneyValueField(help_text=_("The fixed cost to apply to this service."))
    description = TranslatedField(any_language=True)

    translations = TranslatedFields(
        description=models.CharField(
            max_length=100,
            blank=True,
            verbose_name=_("description"),
            help_text=_("The order line text to display when this behavior is applied."),
        ),
    )

    def get_costs(self, service, source):
        price = source.create_price(self.price_value)
        description = self.safe_translation_getter("description")
        yield ServiceCost(price, description)


class WaivingCostBehaviorComponent(TranslatableServiceBehaviorComponent):
    name = _("Waiving cost")
    help_text = _(
        "If the total price of the products is less than a waive limit " "add cost to the price of the service."
    )

    price_value = MoneyValueField(
        help_text=_("The cost to apply to this service if the total price is below the waive limit.")
    )
    waive_limit_value = MoneyValueField(
        help_text=_("The total price of products limit, at which this service cost is waived.")
    )
    description = TranslatedField(any_language=True)

    translations = TranslatedFields(
        description=models.CharField(
            max_length=100,
            blank=True,
            verbose_name=_("description"),
            help_text=_("The order line text to display when this behavior is applied."),
        ),
    )

    def get_costs(self, service, source):
        waive_limit = source.create_price(self.waive_limit_value)
        product_total = source.total_price_of_products
        price = source.create_price(self.price_value)
        description = self.safe_translation_getter("description")
        zero_price = source.create_price(0)
        if product_total and product_total >= waive_limit:
            yield ServiceCost(zero_price, description, base_price=price)
        else:
            yield ServiceCost(price, description)


class WeightLimitsBehaviorComponent(ServiceBehaviorComponent):
    name = _("Weight limits")
    help_text = _("Limit availability of the service based on " "total weight of the products.")

    min_weight = models.DecimalField(
        max_digits=36,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_("minimum weight"),
        help_text=_("The minimum weight required for this service to be available."),
    )
    max_weight = models.DecimalField(
        max_digits=36,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_("maximum weight"),
        help_text=_("The maximum weight allowed by this service."),
    )

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
        "WeightBasedPricingBehaviorComponent", related_name="ranges", on_delete=models.CASCADE
    )
    min_value = MeasurementField(
        unit=settings.SHUUP_MASS_UNIT,
        verbose_name=_("min weight ({})".format(settings.SHUUP_MASS_UNIT)),
        blank=True,
        null=True,
        help_text=_("The minimum weight for this price to apply."),
    )
    max_value = MeasurementField(
        unit=settings.SHUUP_MASS_UNIT,
        verbose_name=_("max weight ({})".format(settings.SHUUP_MASS_UNIT)),
        blank=True,
        null=True,
        help_text=_("The maximum weight before this price no longer applies."),
    )
    price_value = MoneyValueField(help_text=_("The cost to apply to this service when the weight criteria is met."))
    description = TranslatedField(any_language=True)

    translations = TranslatedFields(
        description=models.CharField(
            max_length=100,
            blank=True,
            verbose_name=_("description"),
            help_text=_("The order line text to display when this behavior is applied."),
        ),
    )

    def matches_to_value(self, value):
        return _is_in_range(value, self.min_value, self.max_value)


class WeightBasedPricingBehaviorComponent(ServiceBehaviorComponent):
    name = _("Weight-based pricing")
    help_text = _(
        "Define price based on basket weight. "
        "Range minimums are counted in range only as zero e.g. if there are 2 ranges "
        "(range1 = min 0, max 5; range2 = min 5, max 10), only range1's 'min 0' is going "
        "to be counted, but not range2's 'min 5'."
    )

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
            description = range.safe_translation_getter("description")
            yield ServiceCost(price, description)

    def get_unavailability_reasons(self, service, source):
        range = self._get_matching_range_with_lowest_price(source)
        if not range:
            yield ValidationError(_("Weight does not match with any range."), code="out_of_range")


class GroupAvailabilityBehaviorComponent(ServiceBehaviorComponent):
    name = _("Contact group availability")
    help_text = _("Make service available only for specific contact groups.")

    groups = models.ManyToManyField(
        "ContactGroup", verbose_name=_("groups"), help_text=_("The contact groups for which this service is available.")
    )

    def get_unavailability_reasons(self, service, source):
        if source.customer and not source.customer.pk:
            yield ValidationError(_("Customer does not belong to any group."))
            return

        customer_groups = set(source.customer.groups.all().values_list("pk", flat=True))
        groups_to_match = set(self.groups.all().values_list("pk", flat=True))
        if not bool(customer_groups & groups_to_match):
            yield ValidationError(_("Service is not available for any of the customer's groups."))


class StaffOnlyBehaviorComponent(ServiceBehaviorComponent):
    name = _("Access to Admin Panel only availability")
    help_text = _("Make service available only for people with `Access to Admin Panel` rights.")

    def get_unavailability_reasons(self, service, source):
        if not source.creator or not source.creator.is_staff:
            yield ValidationError(
                _("Service is only available for people with `Access to Admin Panel` (`is_staff`) rights.")
            )


class OrderTotalLimitBehaviorComponent(ServiceBehaviorComponent):
    name = _("Order total price limit")
    help_text = _("Limit service availability based on order's total price.")

    min_price_value = MoneyValueField(blank=True, null=True, verbose_name=_("min price value"))
    max_price_value = MoneyValueField(blank=True, null=True, verbose_name=_("max price value"))

    def get_unavailability_reasons(self, service, source):
        total = source.taxful_total_price.value if source.shop.prices_include_tax else source.taxless_total_price.value
        is_in_range = _is_in_range(total, self.min_price_value, self.max_price_value)
        if not is_in_range:
            yield ValidationError(
                _("Order's total price is not within the defined service limits."), code="order_total_out_of_range"
            )


class CountryLimitBehaviorComponent(ServiceBehaviorComponent):
    name = _("Country limit")
    help_text = _("Limit service availability based on countries selected.")

    available_in_countries = JSONField(blank=True, null=True, verbose_name=_("available in countries"))
    available_in_european_countries = models.BooleanField(default=False, verbose_name=_("available in european union"))
    unavailable_in_countries = JSONField(blank=True, null=True, verbose_name=_("unavailable in countries"))
    unavailable_in_european_countries = models.BooleanField(
        default=False, verbose_name=_("unavailable in european union")
    )

    def get_unavailability_reasons(self, service, source):
        address = source.shipping_address if hasattr(service, "carrier") else source.billing_address
        country = address.country if address else settings.SHUUP_ADDRESS_HOME_COUNTRY
        if not (address or country):
            yield ValidationError(_("Service is not available without a defined country."), code="no_country")

        allowed_countries = self.available_in_countries or []
        if self.available_in_european_countries:
            allowed_countries += REGION_ISO3166["european-union"]

        is_available = bool(country in allowed_countries) if allowed_countries else True

        if is_available:  # Let's see if target country is restricted
            restricted_countries = self.unavailable_in_countries or []
            if self.unavailable_in_european_countries:
                restricted_countries += REGION_ISO3166["european-union"]
            if restricted_countries:
                is_available = bool(country not in restricted_countries)

        if not is_available:
            yield ValidationError(_("Service is not available for this country."), code="invalid_country")


class RoundingMode(Enum):
    ROUND_HALF_UP = decimal.ROUND_HALF_UP
    ROUND_HALF_DOWN = decimal.ROUND_HALF_DOWN
    ROUND_UP = decimal.ROUND_UP
    ROUND_DOWN = decimal.ROUND_DOWN

    class Labels:
        ROUND_HALF_UP = _("round up to the nearest number with ties going up, away from zero")
        ROUND_HALF_DOWN = _("round to the nearest number with ties going down, towards zero")
        ROUND_UP = _("round up, away from zero, towards the farther round number")
        ROUND_DOWN = _("round down, towards zero, towards the closest round number")


def _is_in_range(value, min_value, max_value):
    """
    Help function to check if the range matches with value.

    If min_value is None the max_value determines if the range matches.
    None as a max_value represents infinity. Min value is counted in
    range only when it's zero. Max value is always part of the range.

    :type value: decimal.Decimal
    :type min_value: MeasurementField|MoneyValueField
    :type max_value: MeasurementField|MoneyValueField
    :rtype: bool
    """
    if value is None:
        return False
    if (not (min_value or max_value)) or (min_value == max_value == value):
        return True
    if (not min_value or value > min_value) and (max_value is None or value <= max_value):
        return True
    return False
