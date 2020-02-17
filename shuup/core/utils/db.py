# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import math


def float_wrap(value, func):
    try:
        return func(float(value))
    except:
        return None


def extend_sqlite_functions(connection=None, **kwargs):
    """
    Extends SQLite with trigonometry functions
    """
    if connection and connection.vendor == 'sqlite':
        connection.connection.create_function("sin", 1, lambda x: float_wrap(x, math.sin))
        connection.connection.create_function("cos", 1, lambda x: float_wrap(x, math.cos))
        connection.connection.create_function("acos", 1, lambda x: float_wrap(x, math.acos))
        connection.connection.create_function("degrees", 1, lambda x: float_wrap(x, math.degrees))
        connection.connection.create_function("radians", 1, lambda x: float_wrap(x, math.radians))
