# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import math


def extend_sqlite_functions(connection=None, **kwargs):
    """
    Extends SQLite with trigonometry functions
    """
    if connection and connection.vendor == 'sqlite':
        connection.connection.create_function("sin", 1, math.sin)
        connection.connection.create_function("cos", 1, math.cos)
        connection.connection.create_function("acos", 1, math.acos)
        connection.connection.create_function("degrees", 1, math.degrees)
        connection.connection.create_function("radians", 1, math.radians)
