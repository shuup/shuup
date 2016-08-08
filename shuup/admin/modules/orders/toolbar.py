# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from shuup.admin.toolbar import DropdownItem


class CreatePaymentAction(DropdownItem):
    def __init__(self, object, **kwargs):
        kwargs["url"] = reverse("shuup_admin:order.create-payment", kwargs={"pk": object.pk})
        kwargs["icon"] = "fa fa-money"
        kwargs["text"] = _("Create Payment")
        super(CreatePaymentAction, self).__init__(**kwargs)

    @staticmethod
    def visible_for_object(object):
        return object.can_create_payment()


class CreateShipmentAction(DropdownItem):
    def __init__(self, object, **kwargs):
        kwargs["url"] = reverse("shuup_admin:order.create-shipment", kwargs={"pk": object.pk})
        kwargs["icon"] = "fa fa-truck"
        kwargs["text"] = _("Create Shipment")
        super(CreateShipmentAction, self).__init__(**kwargs)

    @staticmethod
    def visible_for_object(object):
        return object.can_create_shipment()


class CreateRefundAction(DropdownItem):
    def __init__(self, object, **kwargs):
        kwargs["url"] = reverse("shuup_admin:order.create-refund", kwargs={"pk": object.pk})
        kwargs["icon"] = "fa fa-dollar"
        kwargs["text"] = _("Create Refund")
        super(CreateRefundAction, self).__init__(**kwargs)

    @staticmethod
    def visible_for_object(object):
        return object.can_create_refund()
