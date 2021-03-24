# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from copy import deepcopy


def get_templates_setting_for_specific_directories(old_templates_setting, directories):
    templates_setting = deepcopy(old_templates_setting)
    for engine in templates_setting:
        engine["APP_DIRS"] = False
        engine["DIRS"] = directories
    return templates_setting
