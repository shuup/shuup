# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField


class ShopStatus(Enum):
    DISABLED = 0
    ENABLED = 1


@python_2_unicode_compatible
class Shop(TranslatableModel):
    identifier = InternalIdentifierField(unique=True)
    domain = models.CharField(max_length=128, blank=True, null=True, unique=True)
    status = EnumIntegerField(ShopStatus, default=ShopStatus.DISABLED)
    owner = models.ForeignKey("Contact", blank=True, null=True)
    options = JSONField(blank=True, null=True)
    prices_include_tax = models.BooleanField(default=True)

    translations = TranslatedFields(
        name=models.CharField(max_length=64)
    )

    def __str__(self):
        return self.safe_translation_getter("name", default="Shop %d" % self.pk)
