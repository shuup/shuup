# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from shoop.core.order_creator.source import OrderSource


class BasketishOrderSource(OrderSource):

    def __init__(self, lines=()):
        super(BasketishOrderSource, self).__init__()
        self.lines = list(lines)
        for line in self.lines:
            line.source = self

    def get_lines(self):
        return self.lines

    def get_final_lines(self):
        lines = self.get_lines()
        if self.shipping_method:
            lines.extend(self.shipping_method.get_source_lines(source=self))
        if self.payment_method:
            lines.extend(self.payment_method.get_source_lines(source=self))
        return lines
