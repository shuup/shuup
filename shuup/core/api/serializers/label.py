# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from rest_framework import serializers

from shuup.core.models import Label


class LabelSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = Label
        exclude = ("created_on", "modified_on")
