# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.utils.importing import cached_load


def get_basket_order_creator(request):
    return cached_load("SHOOP_BASKET_ORDER_CREATOR_SPEC")(request=request)


def get_basket_view():
    view = cached_load("SHOOP_BASKET_VIEW_SPEC")
    if hasattr(view, "as_view"):  # pragma: no branch
        view = view.as_view()
    return view


def get_basket_command_dispatcher(request):
    """
    :type request: django.http.request.HttpRequest
    :rtype: shoop.front.basket.command_dispatcher.BasketCommandDispatcher
    """
    return cached_load("SHOOP_BASKET_COMMAND_DISPATCHER_SPEC")(request=request)


def get_basket(request):
    """
    :type request: django.http.request.HttpRequest
    :rtype: shoop.front.basket.objects.BaseBasket
    """
    if not hasattr(request, "basket"):
        basket_class = cached_load("SHOOP_BASKET_CLASS_SPEC")
        # This is a little weird in that this is likely to be called from `BasketMiddleware`,
        # which would do the following assignment anyway. However, in case it's _not_ called
        # from there, for some reason, we want to still be able to cache the basket.
        request.basket = basket_class(request)
    return request.basket
