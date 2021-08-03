# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable, Tuple

from shuup.admin.views.select import BaseAdminObjectSelector
from shuup.core.models import Shop


class ShopAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 16
    model = Shop

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """

        qs = Shop.objects.get_for_user(self.user)
        qs = qs.translated(name__icontains=search_term)
        qs = qs.values_list("id", "translations__name")[: self.search_limit]
        return [{"id": id, "name": name} for id, name in list(qs)]
