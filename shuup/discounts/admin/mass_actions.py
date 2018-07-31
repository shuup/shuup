# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from six import string_types

from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.picotable import PicotableMassAction
from shuup.discounts.models import Discount


def _get_query(ids):
    return (Q() if (isinstance(ids, string_types) and ids == "all") else Q(pk__in=ids))


class ArchiveMassAction(PicotableMassAction):
    label = _("Archive Product Discounts")
    identifier = "archive_discounts"

    def process(self, request, ids):
        Discount.objects.active(get_shop(request)).filter(_get_query(ids)).update(active=False)


class UnarchiveMassAction(PicotableMassAction):
    label = _("Unarchive Discounts")
    identifier = "unarchive_discounts"

    def process(self, request, ids):
        Discount.objects.archived(get_shop(request)).filter(_get_query(ids)).update(active=True)


class DeleteMassAction(PicotableMassAction):
    label = _("Delete Discounts")
    identifier = "delete_discounts"

    def process(self, request, ids):
        Discount.objects.archived(get_shop(request)).filter(_get_query(ids)).delete()
