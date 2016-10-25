# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


class CategoryExtensionsAppConfig(AppConfig):
    name = "shuup.category_extensions"
    verbose_name = "Shuup CategoryExtensions"
    label = "category_extensions"
    provides = {
        "admin_category_form_part": [
            "shuup.category_extensions.admin_module.form_parts:AutopopulateFormPart"
        ],
        "category_populator_rule": [
            "shuup.category_extensions.forms:AttributePopulatorRuleForm",
            "shuup.category_extensions.forms:ManufacturerPopulatorRuleForm",
            "shuup.category_extensions.forms:CreationDatePopulatorRuleForm",
        ]
    }
