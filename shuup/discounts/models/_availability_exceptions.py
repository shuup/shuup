# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class AvailabilityException(models.Model):
    shops = models.ManyToManyField("shuup.Shop", blank=True, verbose_name=_("shops"))
    name = models.CharField(
        max_length=120,
        verbose_name=_("name"),
        help_text=_("The name for this exception. Used internally with exception lists for filtering."),
    )
    start_datetime = models.DateTimeField(
        verbose_name=_("start since"),
        help_text=_("Set to restrict the availability exception to be available only after a certain date and time."),
    )
    end_datetime = models.DateTimeField(
        _("end until"),
        help_text=_("Set to restrict the availability exception to be available only until a certain date and time."),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("availability exception")
        verbose_name_plural = _("availability exceptions")
        ordering = ["start_datetime"]
