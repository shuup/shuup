# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from shuup.api.fields import FormattedDecimalField
from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.core.api.front_orders import OrderLineSerializer
from shuup.core.models import OrderLineTax, Tax, TaxClass


class TaxSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Tax)

    class Meta:
        model = Tax
        fields = "__all__"


class TaxSummarySerializer(serializers.Serializer):
    tax_id = serializers.CharField(required=False, allow_null=True)
    tax_code = serializers.CharField(required=False, allow_blank=True)
    tax_name = serializers.CharField(required=False)
    tax_rate = FormattedDecimalField(required=False)
    raw_based_on = FormattedDecimalField(required=False)
    based_on = FormattedDecimalField(required=False)
    tax_amount = FormattedDecimalField(required=False)
    taxful = FormattedDecimalField(required=False)

    def create(self, validated_data):
        from shuup.core.taxing._tax_summary import TaxSummaryLine
        return TaxSummaryLine(**validated_data)

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        return instance


class OrderLineTaxSerializer(serializers.ModelSerializer):
    tax_id = serializers.CharField(required=False)
    tax_code = serializers.CharField(required=False)
    tax = TaxSerializer(read_only=True)
    order_line = OrderLineSerializer(read_only=True)

    class Meta:
        model = OrderLineTax
        fields = "__all__"


class SourceLineTaxSerializer(serializers.Serializer):
    line_id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    amount = FormattedDecimalField(required=True)
    base_amount = FormattedDecimalField(required=True)
    tax = TaxSerializer()


class TaxViewSet(PermissionHelperMixin, ProtectedModelViewSetMixin, ModelViewSet):
    """
    retrieve: Fetches a tax by its ID.

    list: Lists all available taxes.

    delete: Deletes a tax.
    If the object is related to another one and the relationship is protected, an error will be returned.

    create: Creates a new tax.

    update: Fully updates an existing tax.
    You must specify all parameters to make it possible to overwrite all attributes.

    partial_update: Updates an existing tax.
    You can update only a set of attributes.
    """

    queryset = TaxClass.objects.all()
    serializer_class = TaxSerializer

    def get_view_name(self):
        return _("Tax")

    @classmethod
    def get_help_text(cls):
        return _("Taxes can be listed, fetched, created, updated and deleted.")
