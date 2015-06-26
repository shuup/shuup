# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.utils.setup import Setup


def configure(setup):
    from .base_settings import configure as base_configure
    base_configure(setup)
    try:
        from .local_settings import configure as local_configure
    except ImportError:
        pass
    else:
        local_configure(setup)
    return setup

globals().update(Setup.configure(configure))
