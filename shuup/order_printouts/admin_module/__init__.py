# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shuup.admin.base import AdminModule
from shuup.admin.utils.urls import admin_url


class PrintoutsAdminModule(AdminModule):
    def get_urls(self):
        return [
            admin_url(
                "^printouts/delivery/(?P<shipment_pk>\d+)/$",
                "shuup.order_printouts.admin_module.views.get_delivery_pdf",
                name="printouts.delivery_pdf"
            ),
            admin_url(
                "^printouts/confirmation/(?P<order_pk>\d+)/$",
                "shuup.order_printouts.admin_module.views.get_confirmation_pdf",
                name="printouts.confirmation_pdf"
            ),
        ]
