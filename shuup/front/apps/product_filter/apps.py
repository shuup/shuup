# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import shuup.apps


class AppConfig(shuup.apps.AppConfig):
    name = "shuup.front.apps.product_filter"
    label = "product_filter"
    provides = {
        "admin_module": [
            "shuup.front.apps.product_filter.admin:ProductFilterModule"
        ],
        "front_extend_product_list_form": [
            "shuup.front.apps.product_filter.forms.ProductFilterForm",
        ],
        "front_urls": [
            "shuup.front.apps.product_filter.urls.urlpatterns",
        ],
    }
