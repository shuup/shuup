# -*- coding: utf-8 -*-
import six
import abc
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
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


def get_storage():
    """
    Retrieve a basket storage object.

    :return: A basket storage object
    :rtype: BasketStorage
    """
    storage_class = cached_load("SHOOP_BASKET_STORAGE_CLASS_SPEC")
    return storage_class()
