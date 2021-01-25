# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.front.utils.order_source import (
    BaseLinePropertiesDescriptor, LineProperty
)


class TestLinePropertiesDescriptor(BaseLinePropertiesDescriptor):
    @classmethod
    def get_line_properties(cls, line, **kwargs):
        yield LineProperty("Type", str(line.type))
