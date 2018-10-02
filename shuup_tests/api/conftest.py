# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings


ORIGINAL_SETTINGS = []


def pytest_runtest_setup(item):
    global ORIGINAL_SETTINGS
    ORIGINAL_SETTINGS = [item for item in settings.INSTALLED_APPS]
    settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS if "shuup.front" not in app]


def pytest_runtest_teardown(item):
    settings.INSTALLED_APPS = [item for item in ORIGINAL_SETTINGS]
