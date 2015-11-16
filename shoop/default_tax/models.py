# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import CustomerTaxGroup, Tax, TaxClass
from shoop.utils.patterns import pattern_matches


@python_2_unicode_compatible
class TaxRule(models.Model):
    enabled = models.BooleanField(default=True, verbose_name=_('enabled'), db_index=True)
    tax_classes = models.ManyToManyField(
        TaxClass,
        verbose_name=_("Tax classes"), help_text=_(
            "Tax classes of the items to be taxed"))
    customer_tax_groups = models.ManyToManyField(
        CustomerTaxGroup, blank=True,
        verbose_name=_("Customer tax groups"))
    country_codes_pattern = models.CharField(
        max_length=300, blank=True,
        verbose_name=_("Country codes pattern"))
    region_codes_pattern = models.CharField(
        max_length=500, blank=True,
        verbose_name=_("Region codes pattern"))
    postal_codes_pattern = models.CharField(
        max_length=500, blank=True,
        verbose_name=_("Postal codes pattern"))
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
    tax = models.ForeignKey(Tax, on_delete=models.PROTECT)

    def matches(self, taxing_context):
        """
        Check if this tax rule matches given taxing context.

        :type taxing_context: shoop.core.taxing.TaxingContext
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

    def __str__(self):
        return _("Tax rule {} ({})").format(self.pk, self.tax)
