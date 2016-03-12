# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class SocialMediaAppConfig(AppConfig):
    name = "shoop.social_media"
    verbose_name = "Shoop Social Media"
    label = "social_media"
    provides = {
        "admin_module": [
            "shoop.social_media.admin_module:SocialMediaAdminModule",
        ],
    }
