# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

EDIT_FLAG_NAME = "shoop_xtheme_edit"


def could_edit(request):
    """
    Return true if the context of the given request would allow Xtheme editing.

    :param request: HTTP request
    :type request: django.http.HttpRequest
    :return: Would allow editing?
    :rtype: bool
    """
    # TODO: Possibly other conditions?
    return (request.user.is_superuser or request.user.is_staff)


def is_edit_mode(request):
    """
    Return true if the given request has xtheme editing enabled.

    :param request: HTTP request
    :type request: django.http.HttpRequest
    :return: In edit mode?
    :rtype: bool
    """
    return bool(could_edit(request) and request.session.get(EDIT_FLAG_NAME))


def set_edit_mode(request, flag):
    """
    Enable or disable edit mode for the request.

    :param request: HTTP request
    :type request: django.http.HttpRequest
    :param flag: Enable flag
    :type flag: bool
    """
    if flag and could_edit(request):
        request.session[EDIT_FLAG_NAME] = True
    else:
        request.session.pop(EDIT_FLAG_NAME, None)
