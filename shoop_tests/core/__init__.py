# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shoop.apps


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    label = 'shoop_tests_core'

    provides = {
        "module_test_module": [
            __name__ + ".module_test_module:ModuleTestModule",
            __name__ + ".module_test_module:AnotherModuleTestModule",
        ]
    }


default_app_config = __name__ + ".AppConfig"
