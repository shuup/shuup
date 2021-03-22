# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models.signals import post_save

from .models import GDPRSettings, get_setting


def handle_settings_post_save(sender, instance, **kwargs):
    get_setting.cache_clear()


post_save.connect(handle_settings_post_save, sender=GDPRSettings, dispatch_uid="shuup_gdpr:handle_settings_post_save")
