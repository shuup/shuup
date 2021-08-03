# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable, Tuple

from shuup.admin.views.select import BaseAdminObjectSelector
from shuup.core.models import CustomerTaxGroup, Tax, TaxClass


class TaxAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 18
    model = Tax

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = (
            Tax.objects.exclude(enabled=False)
            .translated(name__icontains=search_term)
            .values_list("id", "translations__name")[: self.search_limit]
        )
        return [{"id": id, "name": name} for id, name in list(qs)]


class CustomerTaxGroupAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 18
    model = CustomerTaxGroup

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = CustomerTaxGroup.objects.translated(name__icontains=search_term).values_list("id", "translations__name")[
            : self.search_limit
        ]
        return [{"id": id, "name": name} for id, name in list(qs)]


class TaxClassAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 19
    model = TaxClass

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = TaxClass.objects.translated(name__icontains=search_term).values_list("id", "translations__name")[
            : self.search_limit
        ]
        return [{"id": id, "name": name} for id, name in list(qs)]
