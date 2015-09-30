# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
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


class BasketStorage(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def load(self, basket):  # pragma: no cover
        """
        Load the given basket's data dictionary from the storage.

        :type basket: shoop.front.basket.objects.BaseBasket
        """
        return {}

    @abc.abstractmethod
    def save(self, basket, data):  # pragma: no cover
        """
        Save the given data dictionary into the storage for the given basket.

        :type basket: shoop.front.basket.objects.BaseBasket
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
        basket.request.session[basket.basket_name] = data

    def load(self, basket):
        return basket.request.session.get(basket.basket_name) or {}

    def delete(self, basket):
        basket.request.session.pop(basket.basket_name, None)


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
        product_ids = set(basket.get_product_ids_and_quantities().keys())
        stored_basket.products = product_ids
        basket_get_kwargs = {"pk": stored_basket.pk, "key": stored_basket.key}
        request.session[self._get_session_key(basket)] = basket_get_kwargs

    def load(self, basket):
        stored_basket = self._get_stored_basket(basket)
        return stored_basket.data or {}

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
            stored_basket = StoredBasket()
        return stored_basket


def get_storage():
    """
    Retrieve a basket storage object.

    :return: A basket storage object
    :rtype: BasketStorage
    """
    storage_class = cached_load("SHOOP_BASKET_STORAGE_CLASS_SPEC")
    return storage_class()
