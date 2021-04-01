# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.admin.base import MenuEntry


class BreadcrumbedView(object):
    def get_breadcrumb_parents(self):
        return [MenuEntry(text=self.parent_name, url=self.parent_url)]
