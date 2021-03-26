# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import os
import re
import six
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from jinja2.utils import contextfunction
from logging import getLogger

from shuup.core import cache
from shuup.core.fields import TaggedJSONEncoder
from shuup.core.shop_provider import get_shop
from shuup.utils.django_compat import force_text
from shuup.xtheme.utils import get_html_attrs

LOGGER = getLogger(__name__)

LOCATION_INFO = {
    "head_end": {"name": _("End of head"), "regex": re.compile(r"</head>", re.I), "placement": "pre"},
    "head_start": {"name": _("Start of head"), "regex": re.compile(r"<head[^>]*>", re.I), "placement": "post"},
    "body_end": {"name": _("End of body"), "regex": re.compile(r"</body>", re.I), "placement": "pre"},
    "body_start": {"name": _("Start of body"), "regex": re.compile(r"<body[^>]*>", re.I), "placement": "post"},
    "content_start": {"name": _("Content start"), "regex": re.compile(r"^.*", re.I), "placement": "pre"},
    "content_end": {"name": _("Content end"), "regex": re.compile(r".*$", re.I), "placement": "post"},
}

KNOWN_LOCATIONS = set(LOCATION_INFO.keys())

RESOURCE_CONTAINER_VAR_NAME = "_xtheme_resources"
GLOBAL_SNIPPETS_CACHE_KEY = "global_snippets_{shop_id}"


class InlineScriptResource(six.text_type):
    """
    An inline script resource (a subclass of string).

    The contents are rendered inside a ``<script>`` tag.
    """

    @classmethod
    def from_vars(cls, var_name, *args, **kwargs):
        """
        Create an InlineScriptResource assigning an object of variables into a name in the `window` scope.

        Aside from ``var_name`` the signature of this function is similar to that of ``dict``.
        Useful for configuration options, etc.

        :param var_name: The variable to add into global scope.
        :type var_name: str
        :return: An `InlineScriptResource` object.
        :rtype: InlineScriptResource
        """
        ns = dict(*args, **kwargs)
        return cls("window.%s = %s;" % (var_name, TaggedJSONEncoder().encode(ns)))


class JinjaMarkupResource(object):
    """
    A Jinja markup resource.
    """

    def __init__(self, template, context):
        self.template = template
        self.context = context

    def __str__(self):
        return self.template

    def render(self):
        template = force_text(self.template)
        if not template:
            return template

        from django.template import engines

        for engine_name in engines:
            engine = engines[engine_name]
            try:
                return engine.env.from_string(template).render(self.context)
            except Exception:
                LOGGER.exception("Error! Failed to render Jinja string in Snippet plugin.")
                return force_text(_("(Error while rendering.)"))

    def __eq__(self, other):
        return self.render() == other


class InlineMarkupResource(six.text_type):
    """
    An inline markup resource (a subclass of string).

    The contents are rendered as-is.
    """


class InlineStyleResource(six.text_type):
    """
    An inline style resource (a subclass of string).
    """


class ResourceContainer(object):
    """
    ResourceContainers deal with storing and rendering injected resources.

    A ResourceContainer is injected into rendering contexts by
    `~shuup.xtheme.engine.XthemeTemplate` (akin to how `django-jinja`'s Template injects
    `request` and `csrf_token`).
    """

    def __init__(self):
        self.resources = {}

    def add_resource(self, location, resource):
        """
        Add a resource into the given location.

        Duplicate resources are ignored (and false is returned). Resource injection order is retained.

        :param location: The name of the location. See KNOWN_LOCATIONS.
        :type location: str
        :param resource: The actual resource. Either an URL string or one of the inline resource classes.
        :type resource: str|InlineMarkupResource|InlineScriptResource
        :return: Success flag.
        :rtype: bool
        """
        if not resource:
            return False
        if location not in KNOWN_LOCATIONS:
            raise ValueError("Error! `%r` is not a known xtheme resource location." % location)
        lst = self.resources.setdefault(location, [])
        if resource not in lst:
            lst.append(resource)
            return True
        return False

    def render_resources(self, location, clean=True):
        """
        Render the resources for the given location, then (by default) clean that list of resources.

        :param location: The name of the location. See `KNOWN_LOCATIONS`.
        :type location: str
        :param clean: Whether or not to clean up the list of resources.
        :type clean: bool
        :return: String of HTML.
        """
        lst = self.resources.get(location)
        if not lst:
            return ""
        content = "".join(self._render_resource(resource) for resource in lst)
        if clean:  # pragma: no branch
            self.resources.pop(location, None)
        return mark_safe(content)

    def _render_resource(self, resource):
        """
        Render a single resource.

        :param resource: The resource.
        :type resource: str|InlineMarkupResource|InlineScriptResource
        :return: String of HTML.
        """
        if not resource:  # pragma: no cover
            return ""

        if isinstance(resource, JinjaMarkupResource):
            return resource.render()

        if isinstance(resource, InlineMarkupResource):
            return force_text(resource)

        if isinstance(resource, InlineStyleResource):
            return '<style type="text/css">%s</style>' % resource

        if isinstance(resource, InlineScriptResource):
            return "<script>%s</script>" % resource

        resource = force_text(resource)

        from six.moves.urllib.parse import urlparse

        file_path = urlparse(resource)
        file_name = os.path.basename(file_path.path)

        if file_name.endswith(".js"):
            return "<script%s></script>" % get_html_attrs({"src": resource})

        if file_name.endswith(".css"):
            return "<link%s>" % get_html_attrs({"href": resource, "rel": "stylesheet"})

        return "<!-- (unknown resource type: %s) -->" % escape(resource)


@contextfunction
def inject_resources(context, content, clean=True):
    """
    Inject all the resources in the context's `ResourceContainer` into appropriate places in the content given.

    :param context: Rendering context.
    :type context: jinja2.runtime.Context
    :param content: HTML content.
    :type content: str
    :param clean: Clean the resource container as we go?
    :type clean: bool
    :return: Possibly modified HTML content.
    :rtype: str
    """
    rc = get_resource_container(context)
    if not rc:  # No resource container? Well, whatever.
        return content

    for location_name, location in LOCATION_INFO.items():
        if not rc.resources.get(location_name):
            continue

        injection = rc.render_resources(location_name, clean=clean)
        if not injection:
            continue

        match = location["regex"].search(content)
        if not match:
            continue

        start = match.start()
        end = match.end()

        placement = location["placement"]
        if placement == "pre":
            content = content[:start] + injection + content[start:]
        elif placement == "post":
            content = content[:end] + injection + content[end:]
        else:  # pragma: no cover
            raise ValueError("Error! Unknown placement `%s`." % placement)

    return content


def get_resource_container(context):
    """
    Get a `ResourceContainer` from a rendering context.

    :param context: Context.
    :type context: jinja2.runtime.Context
    :return: Resource Container.
    :rtype: shuup.xtheme.resources.ResourceContainer|None
    """
    return context.get(RESOURCE_CONTAINER_VAR_NAME)


@contextfunction
def add_resource(context, location, resource):
    """
    Add an Xtheme resource into the given context.

    :param context: Context.
    :type context: jinja2.runtime.Context
    :param location: Location string (see `KNOWN_LOCATIONS`).
    :type location: str
    :param resource: Resource descriptor (URL or inline markup object).
    :type resource: str|InlineMarkupResource|InlineScriptResource
    :return: Success flag.
    :rtype: bool
    """
    rc = get_resource_container(context)
    if rc:
        return bool(rc.add_resource(location, resource))
    return False


def valid_view(context):
    """
    Prevent adding the global snippet in admin views and in editor view.
    """
    view_class = getattr(context["view"], "__class__", None) if context.get("view") else None
    request = context.get("request")
    if not (view_class and request):
        return False

    match = request.resolver_match
    if not (match and match.app_name != "shuup_admin"):
        return False

    from shuup.xtheme.views.editor import EditorView

    if issubclass(view_class, EditorView):
        return False

    return True


def inject_global_snippet(context, content):
    if not valid_view(context):
        return

    from shuup.xtheme import get_current_theme
    from shuup.xtheme.models import Snippet, SnippetType

    request = context["request"]
    shop = getattr(request, "shop", None) or get_shop(context["request"])

    cache_key = GLOBAL_SNIPPETS_CACHE_KEY.format(shop_id=shop.id)
    snippets = cache.get(cache_key)

    if snippets is None:
        snippets = Snippet.objects.filter(shop=shop)
        cache.set(cache_key, snippets)

    for snippet in snippets:
        if snippet.themes:
            current_theme = getattr(request, "theme", None) or get_current_theme(shop)
            if current_theme and current_theme.identifier not in snippet.themes:
                continue

        content = snippet.snippet
        if snippet.snippet_type == SnippetType.InlineJS:
            content = InlineScriptResource(content)
        elif snippet.snippet_type == SnippetType.InlineCSS:
            content = InlineStyleResource(content)
        elif snippet.snippet_type == SnippetType.InlineHTMLMarkup:
            content = InlineMarkupResource(content)
        elif snippet.snippet_type == SnippetType.InlineJinjaHTMLMarkup:
            context = dict(context.items())
            # prevent recursive injection
            context["allow_resource_injection"] = False
            content = JinjaMarkupResource(content, context)

        add_resource(context, snippet.location, content)
