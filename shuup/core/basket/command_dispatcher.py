# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from shuup.apps.provides import get_provide_objects
from shuup.core.basket import commands
from shuup.core.basket.command_middleware import BaseBasketCommandMiddleware
from shuup.core.signals import get_basket_command_handler
from shuup.utils.django_compat import force_text
from shuup.utils.excs import Problem


class BasketCommandDispatcher(object):
    """
    BasketCommandDispatcher handles (usually AJAX) requests that somehow update the basket.
    You should never instantiate BasketCommandDispatcher yourself -- instead use
    `get_basket_command_dispatcher()`.

    All `handle_*` methods are expected to accept `**kwargs`.
    """

    commands_module = commands

    def __init__(self, request, basket=None):
        """
        :type request: HttpRequest
        """
        self.request = request
        self.ajax = self.request.is_ajax()
        # :type self.basket: BaseBasket
        self.basket = basket or request.basket

    def get_command_handler(self, command):
        handler = getattr(self.commands_module, "handle_%s" % command.lower(), None)
        if handler and callable(handler):
            return handler

        for receiver, handler in get_basket_command_handler.send(
            BasketCommandDispatcher, command=command, instance=self
        ):
            if handler and callable(handler):
                return handler

    def handle(self, command, kwargs=None):
        """
        Dispatch and handle processing of the given command.

        :param command: Name of command to run.
        :type command: unicode
        :param kwargs: Arguments to pass to the command handler. If empty, `request.POST` is used.
        :type kwargs: dict
        :return: response.
        :rtype: HttpResponse
        """

        kwargs = kwargs or dict(six.iteritems(self.request.POST))
        try:
            handler = self.get_command_handler(command)
            if not handler or not callable(handler):
                raise Problem(_("Error! Invalid command `%s`.") % escape(command))
            kwargs.pop("csrfmiddlewaretoken", None)  # The CSRF token should never be passed as a kwarg
            kwargs.pop("command", None)  # Nor the command
            kwargs.update(request=self.request, basket=self.basket)
            kwargs = self.preprocess_kwargs(command, kwargs)

            response = handler(**kwargs) or {}

        except (Problem, ValidationError) as exc:
            if not self.ajax:
                raise
            msg = exc.message if hasattr(exc, "message") else exc
            response = {
                "error": force_text(msg, errors="ignore"),
                "code": force_text(getattr(exc, "code", None) or "", errors="ignore"),
            }

        response = self.postprocess_response(command, kwargs, response)

        if self.ajax:
            return JsonResponse(response)

        return_url = response.get("return") or kwargs.get("return")
        if return_url and return_url.startswith("/"):
            return HttpResponseRedirect(return_url)
        return redirect("shuup:basket")

    def preprocess_kwargs(self, command, kwargs):
        """
        Preprocess kwargs before they are passed to the given `command` handler.
        Useful for subclassing. Must return the new `kwargs`, even if it wasn't
        mutated.

        :param command: The name of the command about to be run.
        :param kwargs: dict of arguments.
        :return: dict of arguments.
        """

        for basket_command_middleware in get_provide_objects("basket_command_middleware"):
            if not issubclass(basket_command_middleware, BaseBasketCommandMiddleware):
                continue

            # create a copy
            kwargs = dict(
                basket_command_middleware().preprocess_kwargs(
                    basket=self.basket, request=self.request, command=command, kwargs=kwargs
                )
            )

        return kwargs

    def postprocess_response(self, command, kwargs, response):
        """
        Postprocess the response dictionary (not a HTTP response!) before it is
        either turned into JSON or otherwise processed (in the case of non-AJAX requests).

        :param command: The command that was run.
        :param kwargs: The actual kwargs the command was run with.
        :param response: The response the command returned.
        :return: The response to be processed and sent to the client.
        """

        for basket_command_middleware in get_provide_objects("basket_command_middleware"):
            if not issubclass(basket_command_middleware, BaseBasketCommandMiddleware):
                continue

            response = dict(
                basket_command_middleware().postprocess_response(
                    basket=self.basket, request=self.request, command=command, kwargs=kwargs, response=response
                )
            )

        return response
