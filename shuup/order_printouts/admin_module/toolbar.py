# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from shuup.admin.toolbar import DropdownActionButton, DropdownItem


class SimplePrintoutsToolbarButton(DropdownActionButton):
    def __init__(self, order, **kwargs):
        self.split_button = None
        kwargs["icon"] = "fa fa-print"
        kwargs["text"] = _("Print")
        kwargs["extra_css_class"] = "btn-info"
        self.order = order
        self.items = self.get_menu_items()
        super(SimplePrintoutsToolbarButton, self).__init__(self.items, **kwargs)

    def get_menu_items(self):
        shipment_items = []
        for shipment_id in self.order.shipments.values_list("pk", flat=True):
            shipment_items.append(
                DropdownItem(
                    text=_("Get Delivery Slip (Shipment %(id)s)") % {"id": shipment_id},
                    icon="fa fa-truck",
                    url=reverse("shuup_admin:printouts.delivery_pdf", kwargs={"shipment_pk": shipment_id})
                )
            )

        return shipment_items + [
            DropdownItem(
                text=_("Get Order Confirmation"),
                icon="fa fa-money",
                url=reverse("shuup_admin:printouts.confirmation_pdf", kwargs={"order_pk": self.order.pk})
            )
        ]
