# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.front.apps.carousel"
    label = "carousel"
    provides = {
        "admin_module": [
            "shuup.front.apps.carousel.admin_module:CarouselModule"
        ],
        "xtheme_plugin": [
            "shuup.front.apps.carousel.plugins:CarouselPlugin",
            "shuup.front.apps.carousel.plugins:BannerBoxPlugin"
        ],
    }
