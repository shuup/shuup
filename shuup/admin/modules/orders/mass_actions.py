# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.translation import ugettext_lazy as _

from shuup.admin.utils.picotable import PicotableMassAction
from shuup.core.models import Order


class CancelOrderAction(PicotableMassAction):
    label = _("Cancel")
    identifier = "mass_action_order_cancel"

    def process(self, request, ids):
        for order in Order.objects.filter(pk__in=ids):
            if not order.can_set_canceled():
                continue
            order.set_canceled()
