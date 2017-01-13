# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import abc
import uuid

import six

from shuup.core.utils.users import real_user_or_none
from shuup.front.models import StoredBasket
from shuup.utils.importing import cached_load


class BasketCompatibilityError(Exception):
    pass


class BasketStorage(six.with_metaclass(abc.ABCMeta)):
    def load(self, basket):
        """
        Load the given basket's data dictionary from the storage.

        :type basket: shuup.front.basket.objects.BaseBasket
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
            raise BasketCompatibilityError(msg)
        price_units_diff = _price_units_diff(stored_basket, basket.shop)
        if price_units_diff:
            msg = "%s %r: Price unit mismatch with Shop (%s)" % (
                type(stored_basket).__name__, stored_basket.id,
                price_units_diff)
            raise BasketCompatibilityError(msg)
        return stored_basket.data or {}

    @abc.abstractmethod
    def _load_stored_basket(self, basket):
        """
        Load stored basket for the given basket from the storage.

        The returned object should have ``id``, ``shop_id``,
        ``currency``, ``prices_include_tax`` and ``data`` attributes.

        :type basket: shuup.front.basket.objects.BaseBasket
        :return: Stored basket or None
        """
        pass

    @abc.abstractmethod
    def save(self, basket, data):  # pragma: no cover
        """
        Save the given data dictionary into the storage for the given basket.

        :type basket: shuup.front.basket.objects.BaseBasket
        :type data: dict
        """
        pass

    @abc.abstractmethod
    def delete(self, basket):  # pragma: no cover
        """
        Delete the basket from storage.

        :type basket: shuup.front.basket.objects.BaseBasket
        """
        pass

    def finalize(self, basket):
        """
        Mark the basket as "finalized" (i.e. completed) in the storage.

        The actual semantics of what finalization does are up to each backend.

        :type basket: shuup.front.basket.objects.BaseBasket
        """
        self.delete(basket=basket)


class DatabaseBasketStorage(BasketStorage):
    def _get_session_key(self, basket):
        return "basket_key:%s" % basket.key

    def save(self, basket, data):
        """
        :type basket: shuup.front.basket.objects.BaseBasket
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
        request.session['basket_key'] = stored_basket.key

    def _load_stored_basket(self, basket):
        return self._get_stored_basket(basket)

    def delete(self, basket):
        stored_basket = self._get_stored_basket(basket)
        if stored_basket and stored_basket.pk:
            stored_basket.deleted = True
            stored_basket.key = uuid.uuid1().hex  # Regenerate a key to avoid clashes
            stored_basket.save()
        basket.request.session.pop(self._get_session_key(basket), None)
        basket.request.session.pop('basket_key', None)

    def finalize(self, basket):
        stored_basket = self._get_stored_basket(basket)
        if stored_basket and stored_basket.pk:
            stored_basket.deleted = True
            stored_basket.finished = True
            stored_basket.save()
        basket.request.session.pop(self._get_session_key(basket), None)
        basket.request.session.pop('basket_key', None)

    def _get_stored_basket(self, basket):
        request = basket.request
        basket_get_kwargs = request.session.get(self._get_session_key(basket)) or {}
        stored_basket = None
        if basket.key:
            basket_get_kwargs['key'] = basket.key
        if basket_get_kwargs:
            stored_basket = StoredBasket.objects.filter(deleted=False, **basket_get_kwargs).first()
        if not stored_basket:
            if basket_get_kwargs:
                request.session.pop(self._get_session_key(basket), None)
            stored_basket = StoredBasket(
                shop=basket.shop,
                key=basket.key,
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
    storage_class = cached_load("SHUUP_BASKET_STORAGE_CLASS_SPEC")
    return storage_class()
