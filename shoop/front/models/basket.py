# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.db import models
from picklefield.fields import PickledObjectField
from shoop.core.fields import InternalIdentifierField


class StoredBasket(models.Model):
    identifier = InternalIdentifierField(blank=False, default=InternalIdentifierField.random_initial(10, 64))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    data = PickledObjectField(compress=True)

    class Meta:
        app_label = "shoop_front"
