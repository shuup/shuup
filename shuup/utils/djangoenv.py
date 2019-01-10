# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import absolute_import

from django.conf import settings


def has_installed(app):
    """
    Returns whether the `app` is installed in Django,
    it means, it is in `INSTALLED_APPS` settings

    :param app: the application identifier like `shuup.front`
    :type app: str
    """
    return app in getattr(settings, "INSTALLED_APPS", [])
