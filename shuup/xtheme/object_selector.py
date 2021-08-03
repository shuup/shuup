# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable, Tuple

from shuup.admin.views.select import BaseAdminObjectSelector
from shuup.xtheme.models import Font


class FontAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 21
    model = Font

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = Font.objects.filter(name__icontains=search_term)
        qs = qs.filter(shop=self.shop)
        qs = qs.values_list("id", "name")[: self.search_limit]

        return [{"id": id, "name": name} for id, name in list(qs)]
