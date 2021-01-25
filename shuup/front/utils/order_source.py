# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable, Union

from shuup.apps.provides import get_provide_objects
from shuup.core.models import OrderLine
from shuup.core.order_creator import SourceLine


class LineProperty:
    name = None
    value = None

    def __init__(self, name, value):
        self.name = name
        self.value = value


class BaseLinePropertiesDescriptor:
    @classmethod
    def get_line_properties(cls, line: Union[OrderLine, SourceLine], **kwargs) -> Iterable[LineProperty]:
        raise NotImplementedError()


def get_line_properties(line: Union[OrderLine, SourceLine]) -> Iterable[LineProperty]:
    line_properties_descriptors = get_provide_objects("front_line_properties_descriptor")

    for line_properties_descriptor in line_properties_descriptors:  # type: Iterable[BaseLinePropertiesDescriptor]
        if not issubclass(line_properties_descriptor, BaseLinePropertiesDescriptor):
            return

        yield from line_properties_descriptor.get_line_properties(line)
