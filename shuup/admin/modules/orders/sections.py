# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from shuup.admin.base import Section
from shuup.core.models import Shipment
from shuup.core.models._orders import OrderLogEntry


class PaymentOrderSection(Section):
    identifier = "payments"
    name = _("Payments")
    icon = "fa-dollar"
    template = "shuup/admin/orders/_detail_payments.jinja"
    order = 1

    @staticmethod
    def visible_for_order(order):
        return order.payments.count() > 0

    @staticmethod
    def get_context_data(order):
        return order.payments.all()


class ContentsOrderSection(Section):
    identifier = "contents"
    name = _("Order Contents")
    icon = "fa-file-text"
    template = "shuup/admin/orders/_order_contents.jinja"
    order = 2

    @staticmethod
    def visible_for_object(order):
        return True

    @staticmethod
    def get_context_data(order):
        return None


class LogEntriesOrderSection(Section):
    identifier = "log_entries"
    name = _("Log Entries")
    icon = "fa-pencil"
    template = "shuup/admin/orders/_order_log_entries.jinja"
    extra_js = "shuup/admin/orders/_order_log_entries_extra_js.jinja"
    order = 3

    @staticmethod
    def visible_for_object(order):
        return True

    @staticmethod
    def get_context_data(order):
        return OrderLogEntry.objects.filter(target=order).order_by("-created_on").all()[:12]
        # TODO: We're currently trimming to 12 entries, probably need pagination


class ShipmentSection(Section):
    identifier = "shipments"
    name = _("Shipments")
    icon = "fa-check-circle"
    template = "shuup/admin/orders/_order_shipments.jinja"
    order = 3

    @staticmethod
    def visible_for_object(order):
        return True

    @staticmethod
    def get_context_data(order):
        return Shipment.objects.filter(order=order).order_by("-created_on").all()
