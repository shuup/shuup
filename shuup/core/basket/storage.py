# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import abc

import six

from shuup.core.models import Basket
from shuup.core.utils.users import real_user_or_none
from shuup.utils.importing import cached_load


class BasketCompatibilityError(Exception):
    pass


class BasketStorage(six.with_metaclass(abc.ABCMeta)):
    def load(self, basket):
        """
        Load the given basket's data dictionary from the storage.

        :type basket: shuup.core.basket.objects.BaseBasket
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
                "Error! Cannot load basket of a different Shop ("
                "%s id=%r with Shop=%s, Dest. Basket Shop=%s)" % (
                    type(stored_basket).__name__,
                    stored_basket.id, stored_basket.shop_id, basket.shop.id))
            raise BasketCompatibilityError(msg)
        price_units_diff = _price_units_diff(stored_basket, basket.shop)
        if price_units_diff:
            msg = "Error! %s %r: Price unit mismatch with Shop (%s)" % (
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

        :type basket: shuup.core.basket.objects.BaseBasket
        :return: Stored basket or None
        """
        pass

    @abc.abstractmethod
    def save(self, basket, data):  # pragma: no cover
        """
        Save the given data dictionary into the storage for the given basket.

        :type basket: shuup.core.basket.objects.BaseBasket
        :type data: dict
        :rtype str:
        :return: The unique identifier of the basket just created
        """
        pass

    @abc.abstractmethod
    def delete(self, basket):  # pragma: no cover
        """
        Delete the basket from storage.

        :type basket: shuup.core.basket.objects.BaseBasket
        """
        pass

    def finalize(self, basket):
        """
        Mark the basket as "finalized" (i.e. completed) in the storage.

        The actual semantics of what finalization does are up to each backend.

        :type basket: shuup.core.basket.objects.BaseBasket
        """
        self.delete(basket=basket)

    def basket_exists(self, key, shop):
        """
        Check if basket exists in the storage.

        For example this is used from API to check whether the basket
        actually exists for certain shop when accessed with key.

        :type key: str
        :type shop: shuup.core.models.Shop
        """
        return False


class BaseDatabaseBasketStorage(BasketStorage):
    model = Basket

    def get_basket_kwargs(self, basket):
        return {}

    def save(self, basket, data):
        """
        :type basket: shuup.core.basket.objects.BaseBasket
        """
        stored_basket = self._load_stored_basket(basket)
        stored_basket.data = data
        stored_basket.taxless_total_price = basket.taxless_total_price_or_none
        stored_basket.taxful_total_price = basket.taxful_total_price_or_none
        stored_basket.product_count = basket.smart_product_count
        stored_basket.customer = (basket.customer or None)
        stored_basket.orderer = (basket.orderer or None)
        stored_basket.creator = real_user_or_none(basket.creator)
        if hasattr(self.model, "supplier") and hasattr(basket, "supplier"):
            stored_basket.supplier = basket.supplier

        stored_basket.class_spec = "%s.%s" % (
            basket.__class__.__module__, basket.__class__.__name__
        )

        stored_basket.save()
        stored_basket.products.set(set(basket.product_ids))
        return stored_basket

    def delete(self, basket):
        stored_basket = self._load_stored_basket(basket)
        if stored_basket and stored_basket.pk:
            stored_basket.deleted = True
            stored_basket.save()

    def finalize(self, basket):
        stored_basket = self._load_stored_basket(basket)
        if stored_basket and stored_basket.pk:
            stored_basket.deleted = True
            stored_basket.finished = True
            stored_basket.save()

    def _load_stored_basket(self, basket):
        basket_get_kwargs = self.get_basket_kwargs(basket)
        stored_basket = None
        if basket_get_kwargs:
            stored_basket = self.model.objects.filter(deleted=False, **basket_get_kwargs).first()
        if not stored_basket:
            stored_basket = self.model(
                shop=basket.shop,
                currency=basket.currency,
                prices_include_tax=basket.prices_include_tax,
            )
        return stored_basket

    def basket_exists(self, key, shop):
        return self.model.objects.filter(key=key, shop=shop).exists()


class DatabaseBasketStorage(BaseDatabaseBasketStorage):
    def get_basket_kwargs(self, basket):
        if basket.key:
            return {"key": basket.key}
        return {}


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

    :return: A basket storage object.
    :rtype: BasketStorage
    """
    storage_class = cached_load("SHUUP_BASKET_STORAGE_CLASS_SPEC")
    return storage_class()
