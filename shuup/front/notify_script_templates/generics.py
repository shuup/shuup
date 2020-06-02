# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.template import loader as template_loader
from django.template.defaultfilters import linebreaksbr
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shuup.front.notify_events import (
    OrderReceived, PaymentCreated, RefundCreated, ShipmentCreated,
    ShipmentDeleted
)
from shuup.notify.script_template.factory import \
    generic_send_email_script_template_factory
from shuup.testing.modules.content.data import ORDER_CONFIRMATION

mark_safe_lazy = lazy(mark_safe, six.text_type)


SHIPMENT_CREATED_EMAIL_TEMPLATE = mark_safe_lazy(_("""<p>Dear {{ order.customer }},</p>
<p>A shipment has been created for your order and here are the details:</p>

{% if shipment.tracking_code %}
<p>Tracking code: {{ shipment.tracking_code }}</p>
{% endif %}

<p>Contents:</p>
<table>
    <thead>
        <tr>
            <th>Product</th>
            <th>Quantity</th>
        </tr>
    </thead>
    <tbody>
{% for shipment_product in shipments.total_products %}
        <tr>
            <td>{{ shipment_product.product }}</td>
            <td>{{ shipment_product.quantity }}</td>
        </tr>
{% endif %}
    </tbody>
</table>
"""))


ShipmentCreatedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="shipment_created_email",
    event=ShipmentCreated,
    name=_("Send Shipment Created Email"),
    description=_("Send an email to customer when a shipment is created."),
    help_text=_("This script will send an email to customer when a shipment of his order has been created."),
    initial={
        "en-subject": _("{{ order.shop }} - Shipment created for order {{ order.identifier }}"),
        "en-body": SHIPMENT_CREATED_EMAIL_TEMPLATE
    }
)

ShipmentDeletedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="shipment_deleted_email",
    event=ShipmentDeleted,
    name=_("Send Shipment Deleted Email"),
    description=_("Send email when a shipment is deleted."),
    help_text=_("This script will send an email to customer or to any configured email "
                "right after a shipment gets deleted."),
    initial={
        "en-subject": _("{{ order.shop }} - Shipment deleted for order {{ order.identifier }}")
    }
)

PaymentCreatedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="payment_created_email",
    event=PaymentCreated,
    name=_("Send Payment Created Email"),
    description=_("Send email to customer when a payment is created."),
    help_text=_("This script will send an email to customer or to any configured email "
                "right after a payment gets created."),
    initial={
        "en-subject": _("{{ order.shop }} - Payment created for order {{ order.identifier }}")
    }
)

RefundCreatedEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="refund_created_email",
    event=RefundCreated,
    name=_("Send Refund Created Email"),
    description=_("Send email when a refund is created."),
    help_text=_("This script will send an email to customer or to any configured email "
                "right after a refund gets created."),
    initial={
        "en-subject": _("{{ order.shop }} - Refund created for order {{ order.identifier }}")
    }
)

OrderConfirmationEmailScriptTemplate = generic_send_email_script_template_factory(
    identifier="order_received_email",
    event=OrderReceived,
    name=_("Send Order Confirmation Email"),
    description=_("Send a confirmation email when the order is created."),
    help_text=_("This script will send an email to customer or to any configured email right after an "
                "order is created. The order contents can be put on email body as well as other "
                "informations like shipping method and payment method."),
    initial={
        "en-subject": ORDER_CONFIRMATION["subject"],
        "en-body": linebreaksbr(template_loader.get_template(ORDER_CONFIRMATION["body_template"]).render())
    }
)
