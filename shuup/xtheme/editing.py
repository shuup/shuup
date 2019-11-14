# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.middleware.csrf import get_token

from shuup.core.utils.static import get_shuup_static_url
from shuup.front.utils.user import is_admin_user
from shuup.utils.django_compat import NoReverseMatch, reverse
from shuup.xtheme.resources import add_resource, InlineScriptResource

from ._theme import get_current_theme

EDIT_FLAG_NAME = "shuup_xtheme_edit"


def could_edit(request):
    """
    Return true if the context of the given request would allow Xtheme editing.

    :param request: HTTP request
    :type request: django.http.HttpRequest
    :return: Would allow editing?
    :rtype: bool
    """
    return is_admin_user(request)


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


def can_edit(context):
    request = context.get("request")
    if not (request and could_edit(request) and may_inject(context)):
        return False

    return bool(get_current_theme(request.shop))


def add_edit_resources(context):
    """
    Possibly inject Xtheme editor injection resources into the given
    context's resources.

    :param context: Jinja rendering context
    :type context: jinja2.runtime.Context
    """
    request = context.get("request")
    if not can_edit(context):
        return

    try:
        command_url = reverse("shuup:xtheme")
        edit_url = reverse("shuup:xtheme_editor")
        inject_snipper = reverse("shuup_admin:xtheme_snippet.list")
    except NoReverseMatch:  # No URLs no resources
        return

    from .rendering import get_view_config  # avoid circular import
    view_config = get_view_config(context)
    theme = get_current_theme(request.shop)
    add_resource(context, "body_end", InlineScriptResource.from_vars("XthemeEditorConfig", {
        "commandUrl": command_url,
        "editUrl": edit_url,
        "injectSnipperUrl": inject_snipper,
        "themeIdentifier": theme.identifier,
        "viewName": view_config.view_name,
        "edit": is_edit_mode(request),
        "csrfToken": get_token(request),
    }))
    add_resource(context, "head_end", get_shuup_static_url("xtheme/editor-injection.css"))
    add_resource(context, "body_end", get_shuup_static_url("xtheme/editor-injection.js"))
