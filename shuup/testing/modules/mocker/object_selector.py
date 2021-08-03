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


class MockAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 50

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.mock"

    def has_permission(self):
        return has_permission(self.user, "mockup.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        return ["first", "second", "third"]
