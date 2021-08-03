# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from typing import Iterable, Tuple

from shuup.admin.views.select import BaseAdminObjectSelector
from shuup.core.models import Carrier, CustomCarrier, PaymentMethod, ShippingMethod


class CarrierAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 13
    model = Carrier

    @classmethod
    def handles_selector(cls, selector):
        if selector == cls.get_selector_for_model(Carrier) or selector == cls.get_selector_for_model(CustomCarrier):
            return True
        return cls.handle_subclass_selector(selector, Carrier)

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """

        qs = Carrier.objects.translated(name__icontains=search_term)
        qs = qs.filter(shops=self.shop)
        if self.supplier:
            qs = qs.filter(supplier=self.supplier)
        qs = qs.values_list("id", "base_translations__name")[: self.search_limit]
        return [{"id": id, "name": name} for id, name in list(qs)]


class PaymentMethodAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 14
    model = PaymentMethod

    @classmethod
    def handles_selector(cls, selector):
        if selector == cls.get_selector_for_model(PaymentMethod):
            return True
        return cls.handle_subclass_selector(selector, PaymentMethod)

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """

        qs = PaymentMethod.objects.translated(name__icontains=search_term)
        qs = qs.filter(shop=self.shop)
        if self.supplier:
            qs = qs.filter(supplier=self.supplier)
        qs = qs.values_list("id", "translations__name")[: self.search_limit]
        return [{"id": id, "name": name} for id, name in list(qs)]


class ShippingMethodAdminObjectSelector(BaseAdminObjectSelector):
    ordering = 15
    model = ShippingMethod

    @classmethod
    def handles_selector(cls, selector):
        if selector == cls.get_selector_for_model(ShippingMethod):
            return True
        return cls.handle_subclass_selector(selector, ShippingMethod)

    def get_objects(self, search_term, *args, **kwargs) -> Iterable[Tuple[int, str]]:
        """
        Returns an iterable of tuples of (id, text)
        """
        qs = ShippingMethod.objects.translated(name__icontains=search_term).values_list("id", "translations__name")[
            : self.search_limit
        ]
        return [{"id": id, "name": name} for id, name in list(qs)]
