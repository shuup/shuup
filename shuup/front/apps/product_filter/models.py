# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from shuup.core.models import (
    Shop,
    Category,
    Attribute,
)


VERTICAL = 1
HORIZONTAL = 2
LAYOUT_CHOICES = (
    (VERTICAL, _("Vertical")),
    (HORIZONTAL, _("Horizontal"))
)


class BasicFilterSettingsModel(models.Model):
    enabled = models.BooleanField(
        _("Enabled"),
        default=False
    )
    layout = models.SmallIntegerField(
        _("Layout"),
        choices=LAYOUT_CHOICES,
        default=1
    )
    shop = models.ForeignKey(
        Shop,
        default=1
    )

    class Meta:
        verbose_name = _("Filter basic settings")
        verbose_name_plural = _("Filter basic settings")


class CategoriesFilterSettingsModel(models.Model):
    category = models.ManyToManyField(
        Category,
        default=1
    )
    shop = models.ForeignKey(
        Shop,
        default=1
    )

    class Meta:
        verbose_name = _("Filter category setting")
        verbose_name_plural = _("Filter categories settings")


BASIC_ATTRIBUTE_FIELDS = [
    'manufacturer_id', 'width', 'height', 'depth', 'net_weight',
    'gross_weight', 'default_price'
]


class BasicAttributesFilterSettingsModel(models.Model):
    attribute_name = models.CharField(
        max_length=60,
    )
    enabled = models.BooleanField(
        _("Enabled"),
        default=True
    )
    shop = models.ForeignKey(
        Shop,
        default=1
    )

    class Meta:
        verbose_name = _("Basic filter attribute setting")
        verbose_name_plural = _("Basic filter attributes settings")


class AttributesFilterSettingsModel(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        default=1
    )
    enabled = models.BooleanField(
        _("Enabled"),
        default=True
    )
    shop = models.ForeignKey(
        Shop,
        default=1
    )

    class Meta:
        verbose_name = _("Filter attribute setting")
        verbose_name_plural = _("Filter attributes settings")
