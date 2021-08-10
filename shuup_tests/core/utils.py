# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.configuration import get as original_configuration_get
from shuup.core.setting_keys import SHUUP_DISCOUNT_MODULES


class modify(object):
    def __init__(self, target, save=False, **attrs):
        self.attrs = attrs
        self.target = target
        self.save = save
        self.old_attrs = {}

    def __enter__(self):
        self.old_attrs = dict((key, getattr(self.target, key, None)) for key in self.attrs)
        for key, value in self.attrs.items():
            setattr(self.target, key, value)
        if self.save:
            self.target.save()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for key, value in self.old_attrs.items():
            setattr(self.target, key, value)
        if self.save:
            self.target.save()


def get_price_display_patched_configuration(shop, key, default=None):
    if key == SHUUP_DISCOUNT_MODULES:
        return []
    return original_configuration_get(shop, key, default)


def get_pricing_discounts_patched_configuration(shop, key, default=None):
    if key == SHUUP_DISCOUNT_MODULES:
        return ["minus25"]
    return original_configuration_get(shop, key, default)
