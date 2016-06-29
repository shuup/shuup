# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.apps import AppConfig


class ShuupSimpleSupplierAppConfig(AppConfig):
    name = "shuup.simple_supplier"
    verbose_name = "Shuup Simple Supplier"
    label = "simple_supplier"
    provides = {
        "supplier_module": [
            "shuup.simple_supplier.module:SimpleSupplierModule"
        ],
        "admin_product_form_part": [
            "shuup.simple_supplier.admin_module.forms:SimpleSupplierFormPart"
        ],
        "admin_module": [
            "shuup.simple_supplier.admin_module:StocksAdminModule"
        ]
    }

default_app_config = "shuup.simple_supplier.ShuupSimpleSupplierAppConfig"
