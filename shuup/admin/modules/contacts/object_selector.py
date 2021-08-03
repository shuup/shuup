# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from typing import Iterable, Tuple

from shuup.admin.views.select import BaseAdminObjectSelector
from shuup.core.models import CompanyContact, Contact, PersonContact


class ContactAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 3
    model = Contact

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = Contact.objects.filter(email__icontains=search_term).values_list("pk", "email")[: self.search_limit]
        qs = qs.filter(shops=self.shop)

        return [{"id": id, "name": name} for id, name in list(qs)]


class PersonContactAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 4
    model = PersonContact

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = PersonContact.objects.filter(
            Q(email__icontains=search_term) | Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term)
        )
        qs = qs.filter(is_active=True)
        qs = qs.filter(shops=self.shop)
        qs = qs.values_list("pk", "name")[: self.search_limit]

        return [{"id": id, "name": name} for id, name in list(qs)]


class CompanyContactAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 5
    model = CompanyContact

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = CompanyContact.objects.filter(Q(name__icontains=search_term) | Q(email__icontains=search_term))
        qs = qs.filter(shops=self.shop)
        qs = qs.values_list("pk", "name")[: self.search_limit]
        return [{"id": id, "name": name} for id, name in list(qs)]
