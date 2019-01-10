# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django
import django.db.models


def get_managers_for_migration():
    if django.VERSION > (1, 9) and django.VERSION < (1, 11):
        return [('_default_manager', django.db.models.manager.Manager())]
    return []
