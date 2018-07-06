# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup import configuration


def is_tour_complete(shop, tour_key):
    """
    Check if the tour is complete

    :param tour_key: The tour key.
    :type field: str
    :return: whether tour is complete
    :rtype: Boolean
    """
    return configuration.get(shop, "shuup_%s_tour_complete" % tour_key, False)
