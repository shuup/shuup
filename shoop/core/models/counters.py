# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField

__all__ = ("Counter", )


class CounterType(Enum):
    ORDER_REFERENCE = 1

    class Labels:
        ORDER_REFERENCE = _('order reference')


class Counter(models.Model):
    id = EnumIntegerField(CounterType, primary_key=True)
    value = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('counter')
        verbose_name_plural = _('counters')

    @classmethod
    def get_and_increment(cls, id):
        counter, created = cls.objects.select_for_update().get_or_create(id=id)
        current = counter.value
        counter.value += 1
        counter.save()
        return current
