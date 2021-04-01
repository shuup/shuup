# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.front.apps.carousel"
    label = "carousel"
    provides = {
        "admin_module": ["shuup.front.apps.carousel.admin_module:CarouselModule"],
        "xtheme_plugin": [
            "shuup.front.apps.carousel.plugins:CarouselPlugin",
            "shuup.front.apps.carousel.plugins:BannerBoxPlugin",
        ],
    }

    def ready(self):
        from shuup.utils.djangoenv import has_installed

        if has_installed("shuup.xtheme"):
            from django.db.models.signals import post_save

            from shuup.xtheme.cache import bump_xtheme_cache

            from .models import Carousel, Slide

            post_save.connect(bump_xtheme_cache, sender=Carousel)
            post_save.connect(bump_xtheme_cache, sender=Slide)
