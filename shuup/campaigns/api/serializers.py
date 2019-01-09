# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from rest_framework import serializers

from shuup.campaigns.models.context_conditions import HourCondition


class HourConditionSerializer(serializers.ModelSerializer):
    days = serializers.SerializerMethodField()

    class Meta:
        model = HourCondition
        fields = ("id", "hour_start", "hour_end", "days")

    def get_days(self, condition):
        return [v for v in map(int, condition.days.split(","))]


class HourBasketConditionSerializer(serializers.ModelSerializer):
    days = serializers.SerializerMethodField()

    class Meta:
        model = HourCondition
        fields = ("id", "hour_start", "hour_end", "days")

    def get_days(self, condition):
        return [v for v in map(int, condition.days.split(","))]
