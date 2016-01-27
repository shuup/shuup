# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from shoop.apps.provides import load_module_instances


def get_order_source_modifier_modules():
    """
    Get a list of configured order source modifier module instances.

    :rtype: list[OrderSourceModifierModule]
    """
    return load_module_instances(
        "SHOOP_ORDER_SOURCE_MODIFIER_MODULES", "order_source_modifier_module")


class OrderSourceModifierModule(object):
    def get_new_lines(self, order_source, lines):
        """
        Get new lines to be added to order source.

        :type order_source: shoop.core.order_creator.OrderSource
        :type lines: list[shoop.core.order_creator.SourceLine]
        :rtype: Iterable[shoop.core.order_creator.SourceLine]
        """
        return []
