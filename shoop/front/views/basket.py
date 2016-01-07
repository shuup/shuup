# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.views.generic import TemplateView, View

from shoop.front.basket import get_basket_command_dispatcher, get_basket_view


class DefaultBasketView(TemplateView):
    template_name = "shoop/front/basket/default_basket.jinja"

    def get_context_data(self, **kwargs):
        context = super(DefaultBasketView, self).get_context_data()
        basket = self.request.basket  # type: shoop.front.basket.objects.BaseBasket
        context["basket"] = basket
        context["errors"] = list(basket.get_validation_errors())
        return context


class BasketView(View):
    def dispatch(self, request, *args, **kwargs):
        command = request.REQUEST.get("command")
        if command:
            return get_basket_command_dispatcher(request).handle(command)
        else:
            return get_basket_view()(request, *args, **kwargs)
