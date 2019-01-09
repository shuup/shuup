# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


def schema_serializer_class(serializer_class, **kwargs):
    """
    A decorator to set a serializer class in detail or list method of ViewSets
    making it possible to extract the right serializer to generate the proper documentation
    """
    def decorator(func):
        func.schema_serializer_class = serializer_class
        func.kwargs = kwargs
        return func
    return decorator
