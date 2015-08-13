# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.conf import settings
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.utils.crypto import get_random_string

from shoop.core.fields import MoneyField, TaggedJSONField


def generate_key():
    return get_random_string(32)


class StoredBasket(models.Model):
    # A combination of the PK and key is used to retrieve a basket for session situations.
    key = models.CharField(max_length=32, default=generate_key)
    owner_contact = models.ForeignKey("shoop.Contact", blank=True, null=True)
    owner_user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    created_on = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)
    updated_on = models.DateTimeField(auto_now=True, db_index=True, editable=False)
    persistent = models.BooleanField(db_index=True, default=False)
    deleted = models.BooleanField(db_index=True, default=False)
    finished = models.BooleanField(db_index=True, default=False)
    title = models.CharField(max_length=64, blank=True)
    data = TaggedJSONField()

    # For statistics etc., as `data` is opaque:
    taxless_total = MoneyField(default=0, null=True, blank=True)
    taxful_total = MoneyField(default=0, null=True, blank=True)
    product_count = models.IntegerField(default=0)
    products = ManyToManyField("shoop.Product", blank=True)

    class Meta:
        app_label = "shoop_front"
