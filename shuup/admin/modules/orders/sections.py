# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext as _

from shuup.admin.base import Section
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.apps.provides import get_provide_objects
from shuup.core.models import Shipment, Supplier
from shuup.core.models._orders import OrderLogEntry
from shuup.utils.django_compat import reverse


class BasicDetailsOrderSection(Section):
    identifier = "order_details"
    name = _("Details")
    icon = "fa-info-circle"
    template = "shuup/admin/orders/_detail_section.jinja"
    order = 0

    @classmethod
    def visible_for_object(cls, order, request=None):
        return True

    @classmethod
    def get_context_data(cls, order, request=None):
        provided_information = []
        for provided_info in sorted(get_provide_objects("admin_order_information"), key=lambda x: x.order):
            info = provided_info(order)
            if info.provides_info():
                provided_information.append((info.title, info.information))
        return {
            "provided_information": provided_information,
            "multiple_shops_enabled": settings.SHUUP_ENABLE_MULTIPLE_SHOPS,
            "multiple_suppliers_enabled": settings.SHUUP_ENABLE_MULTIPLE_SUPPLIERS,
        }


class PaymentOrderSection(Section):
    identifier = "payments"
    name = _("Payments")
    icon = "fa-dollar"
    template = "shuup/admin/orders/_detail_payments.jinja"
    extra_js = "shuup/admin/orders/_detail_payments_js.jinja"
    order = 1

    @classmethod
    def visible_for_object(cls, order, request=None):
        return order.payments.exists()

    @classmethod
    def get_context_data(cls, order, request=None):
        return order.payments.all()


class ShipmentSection(Section):
    identifier = "shipments_data"
    name = _("Shipments")
    icon = "fa-truck"
    template = "shuup/admin/orders/_order_shipments.jinja"
    order = 2

    @staticmethod
    def visible_for_object(order, request=None):
        if not order.shipping_method:
            return False
        if not order.shipping_method.carrier.uses_default_shipments_manager:
            return False
        return (
            order.has_products_requiring_shipment()
            or Shipment.objects.all_except_deleted().filter(order=order).exists()
        )

    @staticmethod
    def get_context_data(order, request=None):
        suppliers = Supplier.objects.filter(order_lines__order=order).distinct()
        create_permission = "order.create-shipment"
        delete_permission = "order.delete-shipment"
        set_sent_permission = "order.set-shipment-sent"
        missing_permissions = get_missing_permissions(
            request.user, [create_permission, delete_permission, set_sent_permission]
        )
        create_urls = {}
        delete_urls = {}
        set_sent_urls = {}

        if create_permission not in missing_permissions:
            for supplier in suppliers:
                create_urls[supplier.pk] = reverse(
                    "shuup_admin:order.create-shipment", kwargs={"pk": order.pk, "supplier_pk": supplier.pk}
                )

        for shipment_id in order.shipments.all_except_deleted().values_list("id", flat=True):
            if delete_permission not in missing_permissions:
                delete_urls[shipment_id] = reverse("shuup_admin:order.delete-shipment", kwargs={"pk": shipment_id})
            if set_sent_permission not in missing_permissions:
                set_sent_urls[shipment_id] = reverse("shuup_admin:order.set-shipment-sent", kwargs={"pk": shipment_id})

        return {
            "suppliers": suppliers,
            "create_urls": create_urls,
            "delete_urls": delete_urls,
            "set_sent_urls": set_sent_urls,
        }


class LogEntriesOrderSection(Section):
    identifier = "log_entries"
    name = _("Log Entries")
    icon = "fa-pencil"
    template = "shuup/admin/orders/_order_log_entries.jinja"
    extra_js = "shuup/admin/orders/_order_log_entries_extra_js.jinja"
    order = 3

    @classmethod
    def visible_for_object(cls, order, request=None):
        return True

    @classmethod
    def get_context_data(cls, order, request=None):
        return OrderLogEntry.objects.filter(target=order).order_by("-created_on").all()[:12]
        # TODO: We're currently trimming to 12 entries, probably need pagination


class AdminCommentSection(Section):
    identifier = "admin_comment"
    name = _("Admin comment/notes")
    icon = "fa-comment-o"
    template = "shuup/admin/orders/_admin_comment.jinja"
    extra_js = "shuup/admin/orders/_admin_comment_extra_js.jinja"
    order = 4

    @classmethod
    def visible_for_object(cls, order, request=None):
        return True

    @classmethod
    def get_context_data(cls, order, request=None):
        return None
