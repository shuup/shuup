# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings


def get_shuup_volume_unit():
    """
    Return the volume unit that Shuup should use.

    :rtype: str
    """
    return "{}3".format(settings.SHUUP_LENGTH_UNIT)
