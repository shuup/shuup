# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


def _pattern_matches(pattern, target):
    target = "%s" % target
    for pat in pattern.split(","):
        pat = pat.strip()
        if pat == "*" or pat == target:
            return True
        if "-" in pat:
            a, b = pat.split("-", 1)
            if a < target < b:
                return True


PRIORITY_HELP = _(
    'Rules with same priority are value-added (e.g. US taxes) '
    'and rules with different priority are compound taxes '
    '(e.g. Canada Quebec PST case)'
)


@python_2_unicode_compatible
class TaxRule(models.Model):
    enabled = models.BooleanField(default=True, verbose_name=_('enabled'), db_index=True)
    tax_classes = models.ManyToManyField("shoop.TaxClass")
    customer_tax_groups = models.ManyToManyField("shoop.CustomerTaxGroup")
    country_codes_pattern = models.CharField(max_length=300, blank=True)
    region_codes_pattern = models.CharField(max_length=500, blank=True)
    postal_codes_pattern = models.CharField(max_length=500, blank=True)
    # TODO: (TAX) Priority is not supported yet
    priority = models.IntegerField(default=0, help_text=PRIORITY_HELP)
    tax = models.ForeignKey("shoop.Tax")

    def matches(self, taxing_context):
        if self.country_codes_pattern:
            if not _pattern_matches(self.country_codes_pattern, taxing_context.country_code):
                return False
        if self.region_codes_pattern:
            if not _pattern_matches(self.region_codes_pattern, taxing_context.region_code):
                return False
        if self.postal_codes_pattern:
            if not _pattern_matches(self.postal_codes_pattern, taxing_context.postal_code):
                return False
        return True

    def __str__(self):
        tax_classes = sorted(self.tax_classes.values_list("identifier", flat=True))
        customer_tax_groups = sorted(self.customer_tax_groups.values_list("identifier", flat=True))
        return ("%s for %s: %s" % (
            ", ".join(force_text(identifier) for identifier in tax_classes),
            ", ".join(force_text(identifier) for identifier in customer_tax_groups),
            self.tax
        ))
