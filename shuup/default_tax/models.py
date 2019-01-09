# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import CustomerTaxGroup, Tax, TaxClass
from shuup.utils.patterns import Pattern, pattern_matches


class TaxRuleQuerySet(models.QuerySet):
    def may_match_postal_code(self, postalcode):
        null = Q(Q(_postal_codes_min__isnull=True) | Q(_postal_codes_min=""))
        in_range = Q()
        if postalcode:
            in_range = Q(_postal_codes_min__lte=postalcode, _postal_codes_max__gte=postalcode)
        return self.filter(null | in_range)


@python_2_unicode_compatible
class TaxRule(models.Model):
    enabled = models.BooleanField(default=True, verbose_name=_('enabled'), db_index=True, help_text=_(
            "Check this if this tax rule is active."
        )
    )
    tax_classes = models.ManyToManyField(
        TaxClass,
        verbose_name=_("tax classes"), help_text=_(
            "Tax classes of the items to be taxed"))
    customer_tax_groups = models.ManyToManyField(
        CustomerTaxGroup, blank=True,
        verbose_name=_("customer tax groups"),
        help_text=_("The customer tax groups for which this tax rule is limited."))
    country_codes_pattern = models.CharField(
        max_length=300, blank=True,
        verbose_name=_("country codes pattern"))
    region_codes_pattern = models.CharField(
        max_length=500, blank=True,
        verbose_name=_("region codes pattern"))
    postal_codes_pattern = models.TextField(
        blank=True, verbose_name=_("postal codes pattern"))

    _postal_codes_min = models.CharField(max_length=100, blank=True, null=True)
    _postal_codes_max = models.CharField(max_length=100, blank=True, null=True)

    priority = models.IntegerField(
        default=0,
        verbose_name=_("priority"), help_text=_(
            "Rules with same priority define added taxes (e.g. US taxes) "
            "and rules with different priority define compound taxes "
            "(e.g. Canada Quebec PST case)"))
    override_group = models.IntegerField(
        default=0,
        verbose_name=_("override group number"), help_text=_(
            "If several rules match, only the rules with the highest "
            "override group number will be effective.  This can be "
            "used, for example, to implement tax exemption by adding "
            "a rule with very high override group that sets a zero tax."))
    tax = models.ForeignKey(Tax, on_delete=models.PROTECT, verbose_name=_('tax'), help_text=_(
        "The tax to apply when this rule is applied."
    ))

    objects = TaxRuleQuerySet.as_manager()

    def matches(self, taxing_context):
        """
        Check if this tax rule matches given taxing context.

        :type taxing_context: shuup.core.taxing.TaxingContext
        """
        if taxing_context.customer_tax_group:
            tax_groups = set(self.customer_tax_groups.all())
            if tax_groups:
                if taxing_context.customer_tax_group not in tax_groups:
                    return False
        if self.country_codes_pattern:
            if not pattern_matches(self.country_codes_pattern, taxing_context.country_code):
                return False
        if self.region_codes_pattern:
            if not pattern_matches(self.region_codes_pattern, taxing_context.region_code):
                return False
        if self.postal_codes_pattern:
            if not pattern_matches(self.postal_codes_pattern, taxing_context.postal_code):
                return False
        return True

    def save(self, *args, **kwargs):
        min_value, max_value = Pattern(self.postal_codes_pattern).get_alphabetical_limits()
        self._postal_codes_min = min_value
        self._postal_codes_max = max_value
        return super(TaxRule, self).save(*args, **kwargs)

    def __str__(self):
        return _("Tax rule {} ({})").format(self.pk, self.tax)
