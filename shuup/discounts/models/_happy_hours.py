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
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class HappyHour(models.Model):
    shops = models.ManyToManyField("shuup.Shop", blank=True, db_index=True, verbose_name=_("shops"))
    name = models.CharField(
        max_length=120, verbose_name=_("name"),
        help_text=_("The name for this . Used internally with exception lists for filtering."))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("happy hour")
        verbose_name_plural = _("happy hours")


@python_2_unicode_compatible
class TimeRange(models.Model):
    happy_hour = models.ForeignKey("discounts.HappyHour", related_name="time_ranges", verbose_name=_("happy hour"))
    parent = models.ForeignKey(
        "self", blank=True, null=True, related_name="children", on_delete=models.CASCADE, verbose_name=_("parent"))
    from_hour = models.TimeField(verbose_name=_("from hour"), db_index=True)
    to_hour = models.TimeField(verbose_name=_("to hour"), db_index=True)
    weekday = models.IntegerField(verbose_name=_("weekday"), db_index=True)

    def __str__(self):
        return "%s-%s for %s" % (self.weekday, self.pk, self.happy_hour)

    class Meta:
        verbose_name = _('time range')
        verbose_name_plural = _('time ranges')
        ordering = ['weekday', 'from_hour']

    def save(self, **kwargs):
        if self.to_hour < self.from_hour:
            raise ValidationError(_("To hour has to be after from hour"), code="time_range_error")

        return super(TimeRange, self).save(**kwargs)
