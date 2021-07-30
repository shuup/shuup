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


class CouponAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 7

    @classmethod
    def handles_selector(cls, selector):
        return selector == cls.get_selector_for_model(Coupon)

    def has_permission(self):
        return has_permission(self.user, "coupon.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """

        qs = Coupon.objects.exclude(active=False).filter(code__icontains=search_term)
        qs = qs.filter(shop=self.shop)
        if self.supplier:
            qs = qs.filter(supplier=self.supplier)
        qs = qs.values_list("id", "code")[: self.search_limit]
        return [{"id": id, "name": name} for id, name in list(qs)]
