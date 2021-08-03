# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import Group as PermissionGroup
from typing import Iterable, Tuple

from shuup.admin.views.select import BaseAdminObjectSelector


class PermissionGroupAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 9
    model = PermissionGroup

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = PermissionGroup.objects.filter(name__icontains=search_term).values_list("id", "name")[: self.search_limit]
        return [{"id": id, "name": name} for id, name in list(qs)]
