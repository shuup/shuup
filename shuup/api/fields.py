# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from rest_framework import serializers


class EnumField(serializers.ChoiceField):
    """
    A field which accepts django-enumfields types
    """
    def __init__(self, enum, **kwargs):
        self.enum = enum
        kwargs['choices'] = enum.choices()
        super(EnumField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        return self.enum(data)
