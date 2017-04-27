# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from parler_rest.serializers import (
    TranslatableModelSerializer, TranslatedFieldsField
)
from rest_framework.serializers import SerializerMethodField

from shuup.core.models import PaymentMethod, ShippingMethod


class ServiceBaseSerializer(TranslatableModelSerializer):
    price = SerializerMethodField()
    is_available = SerializerMethodField()

    def get_is_available(self, service):
        is_available = None
        source = self.context.get("source")
        if source:
            is_available = service.is_available_for(source)
        return is_available

    def get_price(self, service):
        price = None
        source = self.context.get("source")
        if source:
            price = service.get_total_cost(source).taxful_price.value
        return price


class PaymentMethodSerializer(ServiceBaseSerializer):
    translations = TranslatedFieldsField(shared_model=PaymentMethod, required=False)

    class Meta:
        model = PaymentMethod
        fields = ("__all__")


class ShippingMethodSerializer(ServiceBaseSerializer):
    translations = TranslatedFieldsField(shared_model=ShippingMethod, required=False)

    class Meta:
        model = ShippingMethod
        fields = ("__all__")
