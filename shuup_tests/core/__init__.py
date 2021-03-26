# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


class AppConfig(AppConfig):
    name = "shuup_tests.core"
    label = "shuup_tests_core"

    provides = {
        "module_test_module": [
            "shuup_tests.core.module_test_module:ModuleTestModule",
            "shuup_tests.core.module_test_module:AnotherModuleTestModule",
        ]
    }


default_app_config = "shuup_tests.core.AppConfig"
