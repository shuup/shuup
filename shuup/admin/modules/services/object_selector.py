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
from shuup.core.models import Carrier, PaymentMethod, ShippingMethod


class CarrierAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 13

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.carrier"

    def has_permission(self, user):
        return has_permission(user, "carrier.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        objects = list(
            Carrier.objects.translated(name__icontains=search_term).values_list("id", "base_translations__name")[
                : self.search_limit
            ]
        )
        return [{"id": id, "name": name} for id, name in objects]


class PaymentMethodAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 14

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.paymentmethod"

    def has_permission(self, user):
        return has_permission(user, "payment_method.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        objects = list(
            PaymentMethod.objects.translated(name__icontains=search_term).values_list("id", "translations__name")[
                : self.search_limit
            ]
        )
        return [{"id": id, "name": name} for id, name in objects]


class ShippingMethodAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 15

    @classmethod
    def handles_selector(cls, selector):
        return selector == "shuup.shippingmethod"

    def has_permission(self, user):
        return has_permission(user, "shipping_method.object_selector")

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        objects = list(
            ShippingMethod.objects.translated(name__icontains=search_term).values_list("id", "translations__name")[
                : self.search_limit
            ]
        )
        return [{"id": id, "name": name} for id, name in objects]
