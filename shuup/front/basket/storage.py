# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from shuup.core.basket.storage import BaseDatabaseBasketStorage, BasketStorage
from shuup.front.models import StoredBasket
from shuup.utils.analog import LogEntryKind

LOGGER = logging.getLogger(__name__)


class DirectSessionBasketStorage(BasketStorage):
    def __init__(self):
        if settings.SESSION_SERIALIZER == "django.contrib.sessions.serializers.JSONSerializer":  # pragma: no cover
            raise ImproperlyConfigured(
                "Error! `DirectSessionBasketStorage` will not work with the JSONSerializer session serializer."
            )

    def save(self, basket, data):
        stored_basket = DictStoredBasket.from_basket_and_data(basket, data)
        basket.request.session[basket.basket_name] = stored_basket.as_dict()

    def _load_stored_basket(self, basket):
        stored_basket_dict = basket.request.session.get(basket.basket_name)
        if not stored_basket_dict:
            return None
        return DictStoredBasket.from_dict(stored_basket_dict)

    def delete(self, basket):
        basket.request.session.pop(basket.basket_name, None)


class DictStoredBasket(object):
    def __init__(self, id, shop_id, currency, prices_include_tax, data):
        self.id = id
        self.shop_id = shop_id
        self.currency = currency
        self.prices_include_tax = prices_include_tax
        self.data = data or {}

    @classmethod
    def from_basket_and_data(cls, basket, data):
        return cls(
            id=(getattr(basket, "id", None) or basket.basket_name),
            shop_id=basket.shop.id,
            currency=basket.currency,
            prices_include_tax=basket.prices_include_tax,
            data=data,
        )

    @classmethod
    def from_dict(cls, mapping):
        return cls(**mapping)

    def as_dict(self):
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "currency": self.currency,
            "prices_include_tax": self.prices_include_tax,
            "data": self.data,
        }


class DatabaseBasketStorage(BaseDatabaseBasketStorage):
    model = StoredBasket

    def _get_session_key(self, basket):
        return "basket_%s_key" % basket.basket_name

    def get_basket_kwargs(self, basket):
        # Lets first try to get basket kwargs from basket request session
        basket_kwargs = basket.request.session.get(self._get_session_key(basket))
        if not basket_kwargs:
            # Fallback to basket customer and key combination
            basket_kwargs = {"key": basket.key}
        return basket_kwargs

    def save(self, basket, data):
        stored_basket = super(DatabaseBasketStorage, self).save(basket, data)
        basket_kwargs = {"pk": stored_basket.pk, "key": stored_basket.key}
        basket.request.session[self._get_session_key(basket)] = basket_kwargs

    def delete(self, basket):
        super(DatabaseBasketStorage, self).delete(basket)
        basket.request.session.pop(self._get_session_key(basket), None)

    def finalize(self, basket):
        super(DatabaseBasketStorage, self).finalize(basket)
        basket.request.session.pop(self._get_session_key(basket), None)

    def _load_stored_basket(self, basket):
        stored_basket = super(DatabaseBasketStorage, self)._load_stored_basket(basket)
        if not stored_basket.pk and self.get_basket_kwargs(basket):
            basket.request.session.pop(self._get_session_key(basket), None)
        return stored_basket

    def basket_exists(self, key, shop):
        return self.model.objects.filter(key=key, shop=shop).exists()

    def _get_key_for_logs(self, basket):
        basket_kwargs = self.get_basket_kwargs(basket)
        return "%s%s" % ("stored_basket_key:", basket_kwargs["key"])

    def add_log_entry(self, basket, message, extra={}, kind=LogEntryKind.NOTE):
        try:
            if getattr(basket, "shop", None):
                identifier = self._get_key_for_logs(basket)
                basket.shop.add_log_entry(kind=kind, identifier=identifier, message=message, extra=extra)
        except Exception:
            # This might get called on important checkout related flows it is not
            # good idea to interrupt the business if for some reason this logging
            # fails.
            LOGGER.error("Adding log entry to stored basket failed.")

    def get_log_entries(self, basket):
        identifier = self._get_key_for_logs(basket)
        if getattr(basket, "shop", None):
            return basket.shop.log_entries.filter(identifier=identifier)
        return []
