# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import os

from django.core.exceptions import ImproperlyConfigured

from shuup.utils.setup import Setup

from . import base_settings


def configure(setup):
    base_settings.configure(setup)

    local_settings_file = os.getenv('LOCAL_SETTINGS_FILE')

    # Backward compatibility: Find from current directory, if
    # LOCAL_SETTINGS_FILE environment variables is unset
    if local_settings_file is None:
        cand = os.path.join(os.path.dirname(__file__), 'local_settings.py')
        if os.path.exists(cand):
            local_settings_file = cand

    # Load local settings from file
    if local_settings_file:
        local_settings_ns = {
            '__file__': local_settings_file,
        }
        with open(local_settings_file, 'rb') as fp:
            compiled = compile(fp.read(), local_settings_file, 'exec')
            exec(compiled, local_settings_ns)
        if 'configure' not in local_settings_ns:
            raise ImproperlyConfigured('No configure in local_settings')
        local_configure = local_settings_ns['configure']
        local_configure(setup)

    return setup


globals().update(Setup.configure(configure))
