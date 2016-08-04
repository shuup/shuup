# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.themes.classic_gray"
    label = "shuup.themes.classic_gray"
    provides = {
        "xtheme": "shuup.themes.classic_gray.theme:ClassicGrayTheme",
    }
