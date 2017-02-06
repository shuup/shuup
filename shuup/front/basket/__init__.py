# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
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
    :type request: django.http.request.HttpRequest
    :rtype: shuup.front.basket.objects.BaseBasket
    """
    if basket_name == "basket" and hasattr(request, "basket"):
        return request.basket

    if basket_class is None:
        basket_class = cached_load("SHUUP_BASKET_CLASS_SPEC")

    return basket_class(request, basket_name=basket_name)
