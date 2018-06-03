# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings


def pytest_runtest_setup(item):
    settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS if "shuup.front" not in app]
