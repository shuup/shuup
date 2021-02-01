# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable

from shuup.core.order_creator import SourceLine
from shuup.front.utils.order_source import get_line_properties, LineProperty


def get_properties_from_line(line: SourceLine) -> Iterable[LineProperty]:
    return list(get_line_properties(line))
