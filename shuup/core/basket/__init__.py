# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.utils.importing import cached_load


def get_basket_order_creator(request=None):
    return cached_load("SHUUP_BASKET_ORDER_CREATOR_SPEC")(request=request)


def get_basket_view():
    view = cached_load("SHUUP_BASKET_VIEW_SPEC")
    if hasattr(view, "as_view"):  # pragma: no branch
        view = view.as_view()
    return view


def get_basket_command_dispatcher(request):
    """
    :type request: django.http.request.HttpRequest
    :rtype: shuup.front.basket.command_dispatcher.BasketCommandDispatcher
    """
    return cached_load("SHUUP_BASKET_COMMAND_DISPATCHER_SPEC")(request=request)


def get_basket(request, basket_name="basket", basket_class=None):
    """
    Get the basket cached in the request or create and cache a new one.

    The basket_class is used when creating a new basket, i.e. when the
    request doesn't already have a basket cached with the given name.
    If no basket_class is given, will load a class using the
    `~shuup.front.settings.SHUUP_BASKET_CLASS_SPEC` setting.

    :type request: django.http.request.HttpRequest
    :type basket_name: str
    :type basket_class: type|None
    :rtype: shuup.front.basket.objects.BaseBasket
    """
    basket = _get_basket_from_request(request, basket_name)
    if basket:
        return basket

    if basket_class is None:
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")

    basket = basket_class(request, basket_name=basket_name)

    _save_basket_to_request(request, basket_name, basket)

    return basket


def _get_basket_from_request(request, basket_name):
    if basket_name == "basket":
        return getattr(request, "basket", None)
    else:
        return getattr(request, "baskets", {}).get(basket_name)


def _save_basket_to_request(request, basket_name, basket):
    if basket_name == "basket":
        request.basket = basket
    else:
        if not hasattr(request, "baskets"):
            request.baskets = {}
        request.baskets[basket_name] = basket
