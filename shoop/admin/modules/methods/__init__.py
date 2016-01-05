# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from itertools import chain

from django.utils.translation import ugettext_lazy as _

from shoop.admin.base import AdminModule, MenuEntry
from shoop.admin.utils.urls import admin_url, derive_model_url
from shoop.core.models import PaymentMethod, ShippingMethod


class MethodModule(AdminModule):
    name = _("Methods")

    def _get_per_method_type_urls(self, url_part, class_name_prefix, url_name_prefix):
        ns = {
            "url_part": url_part,
            "class_name_prefix": class_name_prefix,
            "url_name_prefix": url_name_prefix,
        }
        return [
            admin_url(
                "^methods/%(url_part)s/(?P<pk>\d+)/detail/$" % ns,
                "shoop.admin.modules.methods.views.%(class_name_prefix)sEditDetailView" % ns,
                name="%(url_name_prefix)s.edit-detail" % ns
            ),
            admin_url(
                "^methods/%(url_part)s/(?P<pk>\d+)/$" % ns,
                "shoop.admin.modules.methods.views.%(class_name_prefix)sEditView" % ns,
                name="%(url_name_prefix)s.edit" % ns
            ),
            admin_url(
                "^methods/%(url_part)s/new/$" % ns,
                "shoop.admin.modules.methods.views.%(class_name_prefix)sEditView" % ns,
                kwargs={"pk": None},
                name="%(url_name_prefix)s.new" % ns
            ),
            admin_url(
                "^methods/%(url_part)s/$" % ns,
                "shoop.admin.modules.methods.views.%(class_name_prefix)sListView" % ns,
                name="%(url_name_prefix)s.list" % ns
            ),
        ]

    def get_urls(self):
        return list(chain(
            self._get_per_method_type_urls("payment", "PaymentMethod", "method.payment"),
            self._get_per_method_type_urls("shipping", "ShippingMethod", "method.shipping")
        ))

    def get_menu_category_icons(self):
        return {self.name: "fa fa-cubes"}

    def get_menu_entries(self, request):
        category = self.name
        return [
            MenuEntry(
                text=_("Shipping Methods"),
                icon="fa fa-truck",
                url="shoop_admin:method.shipping.list",
                category=category
            ),
            MenuEntry(
                text=_("Payment Methods"),
                icon="fa fa-credit-card",
                url="shoop_admin:method.payment.list",
                category=category
            ),
        ]

    def get_model_url(self, object, kind):
        return (
            derive_model_url(ShippingMethod, "shoop_admin:method.shipping", object, kind) or
            derive_model_url(PaymentMethod, "shoop_admin:method.payment", object, kind)
        )
