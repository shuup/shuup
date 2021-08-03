# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


def get_object_selector_permission_name(model):
    """
    Returns the object selector permission name for the given model
    """
    return "%s.object_selector" % model._meta.model_name
