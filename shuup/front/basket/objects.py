# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from shuup.core.basket.objects import BaseBasket as Basket
from shuup.core.basket.storage import BasketCompatibilityError


class BaseBasket(Basket):
    def __init__(self, request, basket_name="basket"):
        super(BaseBasket, self).__init__(request)
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
