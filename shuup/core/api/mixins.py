# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from rest_framework import serializers

from shuup.core.fields import (
    FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES, FORMATTED_DECIMAL_FIELD_MAX_DIGITS
)


class BaseLineSerializerMixin(serializers.Serializer):
    quantity = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                        decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                     decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    base_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                          decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    discount_amount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                               decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    discounted_unit_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                     decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxful_base_unit_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                      decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxful_discount_amount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                      decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxful_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                            decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxful_discounted_unit_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                            decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    tax_amount = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                          decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    is_discounted = serializers.BooleanField()


class BaseOrderTotalSerializerMixin(serializers.Serializer):
    taxful_total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                  decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    taxless_total_price = serializers.DecimalField(max_digits=FORMATTED_DECIMAL_FIELD_MAX_DIGITS,
                                                   decimal_places=FORMATTED_DECIMAL_FIELD_DECIMAL_PLACES)
    prices_include_tax = serializers.BooleanField()
