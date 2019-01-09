# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from parler_rest.serializers import (
    TranslatableModelSerializer, TranslatedFieldsField
)
from rest_framework import serializers
from rest_framework.fields import empty

from shuup.core.api.serializers import LabelSerializer
from shuup.core.models import (
    PaymentMethod, ServiceBehaviorComponent, ShippingMethod
)


class DynamicBehaviorComponentSerializer(TranslatableModelSerializer):

    class Meta:
        fields = ("__all__")

    def __init__(self, instance=None, data=empty, **kwargs):
        self.Meta.model = instance.__class__
        super(DynamicBehaviorComponentSerializer, self).__init__(instance, data, **kwargs)


class BehaviorComponentSerializer(TranslatableModelSerializer):
    class Meta:
        model = ServiceBehaviorComponent
        fields = ("__all__")

    def to_representation(self, obj):
        """
        Behavior Component representator

        BehaviorComponents are Polymorphic thus it's required to make
        the `to_representation` trick.
        """
        return DynamicBehaviorComponentSerializer(obj, context=self.context).to_representation(obj)


class ServiceBaseSerializer(TranslatableModelSerializer):
    price = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    behavior_components = serializers.SerializerMethodField()
    labels = LabelSerializer(many=True)

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
            price = service.get_total_cost(source).price.value
        return price

    def get_behavior_components(self, service):
        return BehaviorComponentSerializer(service.behavior_components.all(), many=True, context=self.context).data


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
