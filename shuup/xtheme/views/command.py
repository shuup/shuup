# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.http.response import HttpResponseRedirect

from shuup.utils.excs import Problem
from shuup.xtheme.editing import set_edit_mode


def handle_command(request, command):
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


def command_dispatch(request):
    """
    Xtheme command dispatch view.

    :param request: A request
    :type request: django.http.HttpRequest
    :return: A response
    :rtype: django.http.HttpResponse
    """
    command = request.POST.get("command")
    if command:
        response = handle_command(request, command)
        if response:
            return response
    raise Problem("Error! Unknown command: `%r`" % command)
