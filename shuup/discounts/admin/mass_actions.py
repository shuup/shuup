# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from six import string_types

from shuup.admin.shop_provider import get_shop
from shuup.admin.utils.picotable import PicotableMassAction
from shuup.core.utils.price_cache import bump_all_price_caches
from shuup.discounts.models import Discount


def _get_query(ids):
    return (Q() if (isinstance(ids, string_types) and ids == "all") else Q(pk__in=ids))


class ArchiveMassAction(PicotableMassAction):
    label = _("Archive Product Discounts")
    identifier = "archive_discounts"

    def process(self, request, ids):
        shop = get_shop(request)
        Discount.objects.active(shop).filter(_get_query(ids)).update(active=False)
        bump_all_price_caches([shop.pk])


class UnarchiveMassAction(PicotableMassAction):
    label = _("Unarchive Discounts")
    identifier = "unarchive_discounts"

    def process(self, request, ids):
        shop = get_shop(request)
        Discount.objects.archived(shop).filter(_get_query(ids)).update(active=True)
        bump_all_price_caches([shop.pk])


class DeleteMassAction(PicotableMassAction):
    label = _("Delete Discounts")
    identifier = "delete_discounts"

    def process(self, request, ids):
        shop = get_shop(request)
        Discount.objects.archived(shop).filter(_get_query(ids)).delete()
        bump_all_price_caches([shop.pk])
