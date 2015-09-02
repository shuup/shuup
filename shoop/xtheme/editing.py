# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from shoop.xtheme.resources import add_resource, InlineScriptResource

from django.contrib.staticfiles.storage import staticfiles_storage

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
    user = getattr(request, "user", AnonymousUser())
    return (user.is_superuser or user.is_staff)


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


def may_inject(context):
    """
    Figure out if we may inject Xtheme editing into this view.

    The requirements are that there is a CBV `view` object in the
    context, and that `view` object does not explicitly opt-out of
    editing with `xtheme_injection = False`

    :param context: Jinja rendering context
    :type context: jinja2.runtime.Context
    :return: Permission bool
    :rtype: bool
    """
    view = context.get("view")
    return bool(view) and bool(getattr(view, "xtheme_injection", True))


def add_edit_resources(context):
    """
    Possibly inject Xtheme editor injection resources into the given
    context's resources.

    :param context: Jinja rendering context
    :type context: jinja2.runtime.Context
    """
    request = context.get("request")
    if not (request and could_edit(request) and may_inject(context)):
        return
    from .rendering import get_view_config  # avoid circular import
    from .theme import get_current_theme
    view_config = get_view_config(context)
    theme = get_current_theme(request=request)
    if not theme:
        return
    add_resource(context, "body_end", InlineScriptResource.from_vars("XthemeEditorConfig", {
        "commandUrl": "/xtheme/",  # TODO: Use reverse("shoop:xtheme")?
        "editUrl": "/xtheme/editor/",  # TODO: Use reverse("shoop:xtheme")?
        "themeIdentifier": theme.identifier,
        "viewName": view_config.view_name,
        "edit": is_edit_mode(request),
        "csrfToken": get_token(request),
    }))
    add_resource(context, "body_end", staticfiles_storage.url("xtheme/editor-injection.js"))
