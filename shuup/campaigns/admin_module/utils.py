# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.admin.utils.permissions import get_missing_permissions
from shuup.apps.provides import get_provide_objects


def get_formparts_for_provide_key(user, provide_key):
    provide_objects = list(get_provide_objects(provide_key))
    missing_permissions = get_missing_permissions(user, [form.__name__ for form in provide_objects])
    return [provide_object for provide_object in provide_objects if provide_object.__name__ not in missing_permissions]


def get_extra_permissions_for_admin_module():
    # Warning! Only basket campaigns related provides are here since
    # catalog campaigns are deprecated
    provide_keys = [
        "campaign_basket_condition",
        "campaign_basket_discount_effect_form",
        "campaign_basket_line_effect_form",
    ]
    permissions = set()
    for provide_key in provide_keys:
        for provide_object in get_provide_objects(provide_key):
            permissions.add(provide_object.__name__)

    return permissions
