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
from shuup.core.models import Supplier


class SupplierAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 17

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.supplier"

    def has_permission(self, user):
        return has_permission(user, "supplier.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        search_mode = kwargs.get("search_mode")
        shop = kwargs.get("shop")

        qs = Supplier.objects.filter(deleted=False, name__icontains=search_term)
        qs = qs.filter(shops=shop)
        if search_mode == "enabled":
            qs = qs.enabled(shop=shop)
        qs = qs.values_list("id", "name")[: self.search_limit]
        return [{"id": id, "name": name} for id, name in list(qs)]
