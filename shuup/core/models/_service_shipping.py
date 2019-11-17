# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

from django.db import models
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields

from shuup.utils.analog import define_log_model
from shuup.utils.dates import DurationRange

from ._order_lines import OrderLineType
from ._orders import Order
from ._service_base import Service, ServiceChoice, ServiceProvider


class ShippingMethod(Service):
    carrier = models.ForeignKey(
        "Carrier", null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name=_("carrier"))

    translations = TranslatedFields(
        name=models.CharField(max_length=100, verbose_name=_("name"), help_text=_(
                "The shipping method name. This name is shown to the customers on checkout."
            )),
        description=models.CharField(
            max_length=500, blank=True, verbose_name=_("description")), help_text=_(
                "The description of the shipping method. This name is shown to the customers on checkout."
            )
    )

    line_type = OrderLineType.SHIPPING
    shop_product_m2m = "shipping_methods"
    provider_attr = 'carrier'

    class Meta:
        verbose_name = _("shipping method")
        verbose_name_plural = _("shipping methods")

    def can_delete(self):
        return not Order.objects.filter(shipping_method=self).exists()

    def get_shipping_time(self, source):
        """
        Get shipping time for items in given source.

        :rtype: shuup.utils.dates.DurationRange|None
        """
        min_time, max_time = None, None
        for component in self.behavior_components.all():
            delivery_time = component.get_delivery_time(self, source)
            if delivery_time:
                assert isinstance(delivery_time, DurationRange)
                if not max_time or max_time < delivery_time.max_duration:
                    max_time = delivery_time.max_duration
                    min_time = delivery_time.min_duration
        if not max_time:
            return None
        return DurationRange(min_time, max_time)


class Carrier(ServiceProvider):
    """
    Service provider' interface for shipment processing.

    Services provided by a carrier are `shipping methods
    <ShippingMethod>`.  To create a new shipping method for a carrier,
    use the `create_service` method.

    Implementers of this interface will provide a list of
    shipping service choices and each related shipping method should
    have one of those service choices assigned to it.

    Note: `Carrier` objects should never be created on their own, but
    rather through a concrete subclass.
    """

    service_model = ShippingMethod

    def delete(self, *args, **kwargs):
        ShippingMethod.objects.filter(carrier=self).update(**{"enabled": False})
        super(Carrier, self).delete(*args, **kwargs)

    def _create_service(self, choice_identifier, **kwargs):
        labels = kwargs.pop("labels", None)
        service = ShippingMethod.objects.create(
            carrier=self, choice_identifier=choice_identifier, **kwargs)
        if labels:
            service.labels.set(labels)
        return service


class CustomCarrier(Carrier):
    """
    Carrier without any integration or special processing.
    """
    class Meta:
        verbose_name = _("custom carrier")
        verbose_name_plural = _("custom carriers")

    def get_service_choices(self):
        return [ServiceChoice('manual', _("Manually processed shipment"))]


ShippingMethodLogEntry = define_log_model(ShippingMethod)
CarrierLogEntry = define_log_model(Carrier)
