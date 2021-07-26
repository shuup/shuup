# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable, Tuple

from shuup.admin.utils.permissions import has_permission
from shuup.admin.views.select import BaseAdminObjectSelector
from shuup.campaigns.models.campaigns import Coupon
from shuup.discounts.models import Discount


class CouponAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 7

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.coupon"

    def has_permission(self, user):
        return has_permission(user, "coupon.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        objects = list(
            Coupon.objects.filter(code__icontains=search_term).values_list("id", "code")[: self.search_limit]
        )
        return [{"id": id, "name": name} for id, name in objects]


class DiscountAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 8

    @classmethod
    def handles_selector(cls, selector):
        return selector == "discounts.discount"

    def has_permission(self, user):
        return has_permission(user, "discount.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        objects = list(
            Discount.objects.filter(name__icontains=search_term).values_list("id", "name")[: self.search_limit]
        )
        return [{"id": id, "name": name} for id, name in objects]
