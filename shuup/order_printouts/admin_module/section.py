# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import Section


class PrintoutsSection(Section):
    identifier = "printouts_section"
    name = _("Printouts")
    icon = "fa-print"
    template = "shuup/order_printouts/admin/section.jinja"
    order = 5

    @staticmethod
    def visible_for_object(obj):
        return True

    @staticmethod
    def get_context_data(obj):
        return {}
