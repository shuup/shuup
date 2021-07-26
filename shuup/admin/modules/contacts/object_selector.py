# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db.models import Q
from typing import Iterable, Tuple

from shuup.admin.utils.permissions import has_permission
from shuup.admin.views.select import BaseAdminObjectSelector
from shuup.core.models import CompanyContact, Contact, PersonContact


class ContactAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 3

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.%s" % Contact._meta.model_name

    def has_permission(self, user):
        return has_permission(user, "contact.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        shop = kwargs.get("shop")

        qs = Contact.objects.filter(email__icontains=search_term).values_list("pk", "email")[: self.search_limit]
        if shop:
            qs = qs.filter(shops=shop)

        return [{"id": id, "name": name} for id, name in list(qs)]


class PersonContactAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 4

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.%s" % PersonContact._meta.model_name

    def has_permission(self, user):
        return has_permission(user, "personcontact.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        shop = kwargs.get("shop")

        qs = PersonContact.objects.filter(
            Q(email__icontains=search_term) | Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term)
        )
        qs = qs.filter(is_active=True)
        if shop:
            qs = qs.filter(shops=shop)
        qs = qs.values_list("pk", "name")[: self.search_limit]

        return [{"id": id, "name": name} for id, name in list(qs)]


class CompanyContactAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 5

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.%s" % CompanyContact._meta.model_name

    def has_permission(self, user):
        return has_permission(user, "companycontact.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        shop = kwargs.get("shop")

        qs = CompanyContact.objects.filter(Q(name__icontains=search_term) | Q(email__icontains=search_term))
        if shop:
            qs = qs.filter(shops=shop)
        qs = qs.values_list("pk", "name")[: self.search_limit]
        return [{"id": id, "name": name} for id, name in list(qs)]
