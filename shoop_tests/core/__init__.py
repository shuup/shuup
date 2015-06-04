# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class AppConfig(AppConfig):
    name = 'shoop_tests.core'
    label = 'shoop_tests_core'

    provides = {
        "module_test_module": [
            "shoop_tests.core.module_test_module:ModuleTestModule",
            "shoop_tests.core.module_test_module:AnotherModuleTestModule",
        ]
    }


default_app_config = 'shoop_tests.core.AppConfig'
