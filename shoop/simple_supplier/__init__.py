# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.apps import AppConfig


class ShoopSimpleSupplierAppConfig(AppConfig):
    name = "shoop.simple_supplier"
    verbose_name = "Shoop Simple Supplier"
    label = "simple_supplier"
    provides = {
        "supplier_module": [
            "shoop.simple_supplier.module:SimpleSupplierModule"
        ]
    }


default_app_config = "shoop.simple_supplier.ShoopSimpleSupplierAppConfig"
