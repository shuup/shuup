# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import CompanyContact
from shuup.front.utils.dashboard import DashboardItem


class GDPRDashboardItem(DashboardItem):
    title = _("My Data")
    icon = "fa fa-shield"
    _url = "shuup:gdpr_customer_dashboard"

    def show_on_dashboard(self):
        return False

    def get_context(self):
        context = super(GDPRDashboardItem, self).get_context()
        customer = self.request.customer
        context["customer"] = customer
        context["is_company"] = isinstance(customer, CompanyContact)
        return context
