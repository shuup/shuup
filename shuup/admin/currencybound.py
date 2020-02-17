# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from shuup.core.models import Shop


class CurrencyBound(object):
    """
    Mixin for adding currency property defaulting currency of the first Shop.

    The currency property is "lazy" so that database is not accessed on
    initialization, since this mixin will be used by some `AdminModule`
    classes and they will be initialized at import time by
    `module_registry.register` (which is called at import because
    `admin.urls` calls `get_module_urls` at import).
    """
    def __init__(self, currency=None, *args, **kwargs):
        self._currency = currency
        super(CurrencyBound, self).__init__(*args, **kwargs)

    @property
    def currency(self):
        if self._currency is None:
            first_shop = Shop.objects.first()
            if first_shop:
                self._currency = first_shop.currency
        return self._currency
