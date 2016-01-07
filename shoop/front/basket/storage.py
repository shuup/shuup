# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import abc

import six
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from shoop.core.utils.users import real_user_or_none
from shoop.front.models import StoredBasket
from shoop.utils.importing import cached_load


class BasketCompatibilityError(Exception):
    pass


class ShopMismatchBasketCompatibilityError(BasketCompatibilityError):
    pass


class PriceUnitMismatchBasketCompatibilityError(BasketCompatibilityError):
    pass


class BasketStorage(six.with_metaclass(abc.ABCMeta)):
    def load(self, basket):
        """
        Load the given basket's data dictionary from the storage.

        :type basket: shoop.front.basket.objects.BaseBasket
        :rtype: dict
        :raises:
          `BasketCompatibilityError` if basket loaded from the storage
          is not compatible with the requested basket.
        """
        stored_basket = self._load_stored_basket(basket)
        if not stored_basket:
            return {}
        if stored_basket.shop_id != basket.shop.id:
            msg = (
                "Cannot load basket of a different Shop ("
                "%s id=%r with Shop=%s, Dest. Basket Shop=%s)" % (
                    type(stored_basket).__name__,
                    stored_basket.id, stored_basket.shop_id, basket.shop.id))
            raise ShopMismatchBasketCompatibilityError(msg)
        price_unit_diff = _price_units_diff(stored_basket, basket.shop)
        if price_unit_diff:
            msg = "%s %r: Price unit mismatch with Shop (%s)" % (
                type(stored_basket).__name__, stored_basket.id,
                price_unit_diff)
            raise PriceUnitMismatchBasketCompatibilityError(msg)
        return stored_basket.data or {}

    @abc.abstractmethod
    def _load_stored_basket(self, basket):
        """
        Load stored basket for the given basket from the storage.

        The returned object should have ``id``, ``shop_id``,
        ``currency``, ``prices_include_tax`` and ``data`` attributes.

        :type basket: shoop.front.basket.objects.BaseBasket
        :return: Stored basket or None
        """
        pass

    @abc.abstractmethod
    def save(self, basket, data):  # pragma: no cover
        """
        Save the given data dictionary into the storage for the given basket.

        :type basket: shoop.front.basket.objects.BaseBasket
        :type data: dict
        """
        pass

    @abc.abstractmethod
    def delete(self, basket):  # pragma: no cover
        """
        Delete the basket from storage.

        :type basket: shoop.front.basket.objects.BaseBasket
        """
        pass

    def finalize(self, basket):  # pragma: no cover
        """
        Mark the basket as "finalized" (i.e. completed) in the storage.

        The actual semantics of what finalization does are up to each backend.

        :type basket: shoop.front.basket.objects.BaseBasket
        """
        self.delete()


class DirectSessionBasketStorage(BasketStorage):
    def __init__(self):
        if settings.SESSION_SERIALIZER == "django.contrib.sessions.serializers.JSONSerializer":  # pragma: no cover
            raise ImproperlyConfigured(
                "DirectSessionBasketStorage will not work with the JSONSerializer session serializer."
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
        self.data = (data or {})

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


class DatabaseBasketStorage(BasketStorage):
    def _get_session_key(self, basket):
        return "basket_%s_key" % basket.basket_name

    def save(self, basket, data):
        """
        :type basket: shoop.front.basket.objects.BaseBasket
        """
        request = basket.request
        stored_basket = self._get_stored_basket(basket)
        stored_basket.data = data
        stored_basket.taxless_total_price = basket.taxless_total_price_or_none
        stored_basket.taxful_total_price = basket.taxful_total_price_or_none
        stored_basket.product_count = basket.product_count
        stored_basket.customer = (basket.customer or None)
        stored_basket.orderer = (basket.orderer or None)
        stored_basket.creator = real_user_or_none(basket.creator)
        stored_basket.save()
        stored_basket.products = set(basket.product_ids)
        basket_get_kwargs = {"pk": stored_basket.pk, "key": stored_basket.key}
        request.session[self._get_session_key(basket)] = basket_get_kwargs

    def _load_stored_basket(self, basket):
        return self._get_stored_basket(basket)

    def delete(self, basket):
        stored_basket = self._get_stored_basket(basket)
        if stored_basket and stored_basket.pk:
            stored_basket.deleted = True
            stored_basket.save()
        basket.request.session.pop(self._get_session_key(basket), None)

    def finalize(self, basket):
        stored_basket = self._get_stored_basket(basket)
        if stored_basket and stored_basket.pk:
            stored_basket.deleted = True
            stored_basket.finished = True
            stored_basket.save()
        basket.request.session.pop(self._get_session_key(basket), None)

    def _get_stored_basket(self, basket):
        request = basket.request
        basket_get_kwargs = request.session.get(self._get_session_key(basket))
        stored_basket = None
        if basket_get_kwargs:
            stored_basket = StoredBasket.objects.filter(deleted=False, **basket_get_kwargs).first()
        if not stored_basket:
            if basket_get_kwargs:
                request.session.pop(self._get_session_key(basket), None)
            stored_basket = StoredBasket(
                shop=basket.shop,
                currency=basket.currency,
                prices_include_tax=basket.prices_include_tax,
            )
        return stored_basket


def _price_units_diff(x, y):
    diff = []
    if x.currency != y.currency:
        diff.append('currency: %r vs %r' % (x.currency, y.currency))
    if x.prices_include_tax != y.prices_include_tax:
        diff.append('includes_tax: %r vs %r' % (
            x.prices_include_tax, y.prices_include_tax))
    return ', '.join(diff)


def get_storage():
    """
    Retrieve a basket storage object.

    :return: A basket storage object
    :rtype: BasketStorage
    """
    storage_class = cached_load("SHOOP_BASKET_STORAGE_CLASS_SPEC")
    return storage_class()
