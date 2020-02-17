# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import CompanyContact
from shuup.front.utils.companies import allow_company_registration
from shuup.front.utils.dashboard import DashboardItem


class CustomerDashboardItem(DashboardItem):
    template_name = "shuup/customer_information/customer_dashboard_item.jinja"
    title = _("Customer Information")
    icon = "fa fa-user"
    _url = "shuup:customer_edit"

    def get_context(self):
        context = super(CustomerDashboardItem, self).get_context()
        customer = self.request.customer
        context["customer"] = customer
        context["is_company"] = isinstance(customer, CompanyContact)
        return context


class CompanyDashboardItem(DashboardItem):
    title = _("Company Information")
    description = _("Edit Company Information.")
    icon = "fa fa-building"
    _url = "shuup:company_edit"

    def show_on_dashboard(self):
        return False  # Don't show this on menu since we already have all the information there

    def show_on_menu(self):
        # Only show this on menu if customer is company
        return (isinstance(self.request.customer, CompanyContact) or allow_company_registration(self.request.shop))


class AddressBookDashboardItem(DashboardItem):
    title = _("Address Book")
    description = _("Address Book")
    icon = "fa fa-building"
    _url = "shuup:address_book"

    def show_on_dashboard(self):
        return False  # Don't show this on menu since we already have all the information there
