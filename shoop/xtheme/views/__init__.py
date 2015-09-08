# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.http.response import HttpResponseRedirect
from shoop.utils.excs import Problem
from shoop.xtheme.editing import set_edit_mode


def xtheme_dispatch_command(request, command):
    """
    Internal dispatch function.

    :param request: A request
    :type request: django.http.HttpRequest
    :param command: Command string
    :type command: str
    :return: A response
    :rtype: django.http.HttpResponse
    """
    path = request.POST.get("path") or request.META.get("HTTP_REFERER") or "/"
    if command == "edit_on" or command == "edit_off":
        set_edit_mode(request, command.endswith("_on"))
        return HttpResponseRedirect(path)


def xtheme_dispatch(request):
    """
    Xtheme command dispatch view.

    :param request: A request
    :type request: django.http.HttpRequest
    :return: A response
    :rtype: django.http.HttpResponse
    """
    command = request.POST.get("command")
    if command:
        response = xtheme_dispatch_command(request, command)
        if response:
            return response
    raise Problem("Unknown command: %r" % command)
