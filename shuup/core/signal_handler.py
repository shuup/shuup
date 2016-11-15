# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models.signals import post_save
from django.dispatch import receiver

from shuup.core.models._currencies import Currency, override_currency_precision
from shuup.utils.money import make_precision


@receiver(post_save, sender=Currency)
def handle_currency_post_save(sender, instance, **kwargs):
    """
    Handles the Currency post_save signal, updating the
    currency precision's cache.
    """
    override_currency_precision(instance.code, make_precision(instance.decimal_places))
