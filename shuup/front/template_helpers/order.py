# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable

from shuup.core.models import OrderLine
from shuup.front.utils.order_source import LineProperty, get_line_properties


def get_properties_from_line(line: OrderLine) -> Iterable[LineProperty]:
    return list(get_line_properties(line))
