# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import derive_model_url, get_edit_and_list_urls
from shoop.core.models import PaymentMethod, ShippingMethod


class ServiceModule(AdminModule):
    category = _("Payment and Shipping")
    model = None
    name = None
    url_prefix = None
    view_template = None
    name_template = None
    menu_entry_url = None
    url_name_prefix = None

    def get_urls(self):
        return get_edit_and_list_urls(
            url_prefix=self.url_prefix,
            view_template=self.view_template,
            name_template=self.name_template
        )

    def get_menu_entries(self, request):
        return [
            MenuEntry(
                text=self.name,
                url=self.menu_entry_url,
                category=self.category
            )
        ]

    def get_model_url(self, object, kind):
        return derive_model_url(self.model, self.url_name_prefix, object, kind)


class ShippingMethodModule(ServiceModule):
    model = ShippingMethod
    name = _("Shipping Methods")
    url_prefix = "^shipping_methods"
    view_template = "shoop.admin.modules.services.views.ShippingMethod%sView"
    name_template = "shipping_methods.%s"
    menu_entry_url = "shoop_admin:shipping_methods.list"
    url_name_prefix = "shoop_admin:shipping_methods"

    breadcrumbs_menu_entry = MenuEntry(text=name, url="shoop_admin:shipping_methods.list")


class PaymentMethodModule(ServiceModule):
    model = PaymentMethod
    name = _("Payment Methods")
    url_prefix = "^payment_methods"
    view_template = "shoop.admin.modules.services.views.PaymentMethod%sView"
    name_template = "payment_methods.%s"
    menu_entry_url = "shoop_admin:payment_methods.list"
    url_name_prefix = "shoop_admin:payment_methods"

    breadcrumbs_menu_entry = MenuEntry(text=name, url="shoop_admin:payment_methods.list")
