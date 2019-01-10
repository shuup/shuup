# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from shuup import configuration
from shuup.core.basket.objects import BaseBasket as Basket
from shuup.core.basket.storage import BasketCompatibilityError
from shuup.front.checkout.methods import (
    PAYMENT_METHOD_REQUIRED_CONFIG_KEY, SHIPPING_METHOD_REQUIRED_CONFIG_KEY
)


class BaseBasket(Basket):
    def __init__(self, request, basket_name="basket", shop=None, **kwargs):
        super(BaseBasket, self).__init__(request, basket_name, shop)
        self.basket_name = basket_name

    def _load(self):
        """
        Get the currently persisted data for this basket.
        This will only access the storage once per request in usual
        circumstances.
        :return: Data dict.
        :rtype: dict
        """
        if self._data is None:
            try:
                self._data = self.storage.load(basket=self)
            except BasketCompatibilityError as error:
                msg = _("Basket loading failed: Incompatible basket (%s)")
                messages.error(self.request, msg % error)
                self.storage.delete(basket=self)
                self._data = self.storage.load(basket=self)
            self.dirty = False
            self.uncache()
        return self._data

    def get_methods_validation_errors(self):
        shipping_methods = self.get_available_shipping_methods()
        payment_methods = self.get_available_payment_methods()

        advice = _(
            "Try to remove some products from the basket "
            "and order them separately.")

        if (self.has_shippable_lines() and not shipping_methods and
                configuration.get(self.shop, SHIPPING_METHOD_REQUIRED_CONFIG_KEY, True)):
            msg = _("Products in basket cannot be shipped together. %s")
            yield ValidationError(msg % advice, code="no_common_shipping")

        if not payment_methods and configuration.get(self.shop, PAYMENT_METHOD_REQUIRED_CONFIG_KEY, True):
            msg = _("Products in basket have no common payment method. %s")
            yield ValidationError(msg % advice, code="no_common_payment")
