# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from shoop.core.fields import MoneyValueField

__all__ = ("Payment",)


class Payment(models.Model):
    # TODO: Revise!!!
    order = models.ForeignKey("Order", related_name='payments', on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=True)
    gateway_id = models.CharField(max_length=32)  # TODO: do we need this?
    payment_identifier = models.CharField(max_length=96, unique=True)
    amount = MoneyValueField()
    description = models.CharField(max_length=256, blank=True)
    # TODO: Currency here?

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
