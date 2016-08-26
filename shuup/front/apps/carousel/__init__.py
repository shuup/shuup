# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = __name__
    provides = {
        "admin_module": [__name__ + ".admin_module:CarouselModule"],
        "xtheme_plugin": [__name__ + ".plugins:CarouselPlugin",
                          __name__ + ".plugins:BannerBoxPlugin"],
    }

default_app_config = __name__ + ".AppConfig"
