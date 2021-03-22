# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext as _


class EmailTemplate(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=60)
    template = models.TextField(
        verbose_name=_("Template"),
        help_text=_(
            "Enter the base HTML template to be used in emails. "
            "Mark the place to inject the email content using the variable `%html_body%` inside the body."
        ),
    )

    class Meta:
        verbose_name = _("Email Template")
        verbose_name_plural = _("Email Templates")

    def __str__(self):
        return self.name
