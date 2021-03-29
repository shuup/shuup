# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import six


def make_bind_data(variables=None, constants=None):
    if not constants:
        constants = {}
    if not variables:
        variables = {}
    bind_data = {}
    for name, variable in six.iteritems(variables):
        bind_data[name] = {"variable": variable}
    for name, constant in six.iteritems(constants):
        bind_data[name] = {"constant": constant}
    return bind_data
