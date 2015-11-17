# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import shoop.apps
from shoop.apps.settings import validate_templates_configuration


class AppConfig(shoop.apps.AppConfig):
    name = __name__
    verbose_name = "Shoop Admin"
    label = "shoop_admin"
    required_installed_apps = ["bootstrap3"]
    provides = {
        "admin_module": [
            __name__ + ".modules.system:SystemModule",
            __name__ + ".modules.products:ProductModule",
            __name__ + ".modules.product_types:ProductTypeModule",
            __name__ + ".modules.media:MediaModule",
            __name__ + ".modules.orders:OrderModule",
            __name__ + ".modules.taxes:TaxModule",
            __name__ + ".modules.categories:CategoryModule",
            __name__ + ".modules.contacts:ContactModule",
            __name__ + ".modules.contact_groups:ContactGroupModule",
            __name__ + ".modules.users:UserModule",
            __name__ + ".modules.methods:MethodModule",
            __name__ + ".modules.attributes:AttributeModule",
            __name__ + ".modules.sales_units:SalesUnitModule",
            __name__ + ".modules.shops:ShopModule",
            __name__ + ".modules.demo:DemoModule",
            __name__ + ".modules.manufacturers:ManufacturerModule",
            __name__ + ".modules.suppliers:SupplierModule"
        ]
    }

    def ready(self):
        validate_templates_configuration()


default_app_config = __name__ + ".AppConfig"
