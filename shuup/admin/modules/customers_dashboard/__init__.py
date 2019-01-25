# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.translation import ugettext_lazy as _

from shuup.admin.base import AdminModule
from shuup.admin.utils.permissions import get_permission_str
from shuup.core.models import Contact

from .dashboard import get_active_customers_block


class CustomersDashboardModule(AdminModule):
    name = _("Customers Dashboard")

    def get_dashboard_blocks(self, request):
        yield get_active_customers_block(request)

    def get_required_permissions(self):
        return set(get_permission_str(Contact, "view"))  # TODO: This could be a spot for custom admin permission
