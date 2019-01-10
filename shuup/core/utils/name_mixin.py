# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext as _


class NameMixin(object):
    @property
    def split_name(self):
        return (self.name.strip() or _('First Last')).split(None, 1)

    @property
    def first_name(self):
        return self.split_name[0]

    @property
    def last_name(self):
        splitted = self.split_name
        return splitted[-1] if len(splitted) > 1 else ""

    @property
    def full_name(self):
        return (" ".join([self.prefix, self.name, self.suffix])).strip()
