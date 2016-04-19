# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from shoop.core.fields import MoneyValueField
from shoop.core.models import ContactGroup, Shop
from shoop.core.models._contacts import PROTECTED_CONTACT_GROUP_IDENTIFIERS


class SalesRangeQuerySet(models.QuerySet):
    def active(self, shop):
        query = Q(shop=shop)
        # Min value needs to be set
        query &= Q(min_value__isnull=False)
        # If max value is not null it can't be zero
        query &= ~Q(Q(max_value__isnull=False) & Q(max_value=0))
        return self.filter(query)


class ContactGroupSalesRange(models.Model):
    group = models.ForeignKey(ContactGroup, related_name="+", on_delete=models.CASCADE, verbose_name=_("group"))
    shop = models.ForeignKey(Shop, related_name="+", verbose_name=_("shop"))
    min_value = MoneyValueField(verbose_name=_("min amount"), blank=True, null=True)
    max_value = MoneyValueField(verbose_name=_("max amount"), blank=True, null=True)

    objects = SalesRangeQuerySet.as_manager()

    class Meta:
        unique_together = ("group", "shop")

    def save(self, *args, **kwargs):
        self.clean()
        super(ContactGroupSalesRange, self).save(*args, **kwargs)

    def clean(self):
        super(ContactGroupSalesRange, self).clean()
        if self.group.identifier in PROTECTED_CONTACT_GROUP_IDENTIFIERS:
            raise ValidationError(_("Can not add sales limits for default contact groups"))
