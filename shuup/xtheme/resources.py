# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import re

import six
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from jinja2.utils import contextfunction

from shuup.core.fields import TaggedJSONEncoder
from shuup.xtheme.utils import get_html_attrs

LOCATION_INFO = {
    "head_end": (re.compile(r"</head>", re.I), "pre"),
    "body_end": (re.compile(r"</body>", re.I), "pre"),
    "body_start": (re.compile(r"<body[^>]*>", re.I), "post"),
    "content_start": (re.compile(r"^.*", re.I), "pre"),
    "content_end": (re.compile(r".*$", re.I), "post")
}

KNOWN_LOCATIONS = set(LOCATION_INFO.keys())

RESOURCE_CONTAINER_VAR_NAME = "_xtheme_resources"


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

        :param var_name: The variable to add into global scope
        :type var_name: str
        :return: An `InlineScriptResource` object
        :rtype: InlineScriptResource
        """
        ns = dict(*args, **kwargs)
        return cls("window.%s = %s;" % (var_name, TaggedJSONEncoder().encode(ns)))


class InlineMarkupResource(six.text_type):
    """
    An inline markup resource (a subclass of string).

    The contents are rendered as-is.
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
            raise ValueError("%r is not a known xtheme resource location" % location)
        lst = self.resources.setdefault(location, [])
        if resource not in lst:
            lst.append(resource)
            return True
        return False

    def render_resources(self, location, clean=True):
        """
        Render the resources for the given location, then (by default) clean that list of resources.

        :param location: The name of the location. See KNOWN_LOCATIONS.
        :type location: str
        :param clean: Whether or not to clean up the list of resources.
        :type clean: bool
        :return: String of HTML
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
        :return: String of HTML
        """
        if not resource:  # pragma: no cover
            return ""

        if isinstance(resource, InlineMarkupResource):
            return force_text(resource)

        if isinstance(resource, InlineScriptResource):
            return "<script>%s</script>" % resource

        resource = force_text(resource)

        # TODO: should this be extensible?

        if resource.endswith(".js"):
            return "<script%s></script>" % get_html_attrs({"src": resource})

        if resource.endswith(".css"):
            return "<link%s>" % get_html_attrs({"href": resource, "rel": "stylesheet"})

        return "<!-- (unknown resource type: %s) -->" % escape(resource)


@contextfunction
def inject_resources(context, content, clean=True):
    """
    Inject all the resources in the context's ResourceContainer into appropriate places in the content given.

    :param context: Rendering context
    :type context: jinja2.runtime.Context
    :param content: HTML content
    :type content: str
    :param clean: Clean the resource container as we go?
    :type clean: bool
    :return: Possibly modified HTML content
    :rtype: str
    """
    rc = get_resource_container(context)
    if not rc:  # No resource container? Well, whatever.
        return content

    for location_name, (regex, placement) in LOCATION_INFO.items():
        match = regex.search(content)
        if not match:
            continue
        injection = rc.render_resources(location_name, clean=clean)
        if not injection:
            continue

        start = match.start()
        end = match.end()

        if placement == "pre":
            content = content[:start] + injection + content[start:]
        elif placement == "post":
            content = content[:end] + injection + content[end:]
        else:  # pragma: no cover
            raise ValueError("Unknown placement %s" % placement)

    return content


def get_resource_container(context):
    """
    Get a `ResourceContainer` from a rendering context.

    :param context: Context
    :type context: jinja2.runtime.Context
    :return: Resource Container
    :rtype: shuup.xtheme.resources.ResourceContainer|None
    """
    return context.get(RESOURCE_CONTAINER_VAR_NAME)


@contextfunction
def add_resource(context, location, resource):
    """
    Add an Xtheme resource into the given context.

    :param context: Context
    :type context: jinja2.runtime.Context
    :param location: Location string (see KNOWN_LOCATIONS)
    :type location: str
    :param resource: Resource descriptor (URL or inline markup object)
    :type resource: str|InlineMarkupResource|InlineScriptResource
    :return: Success flag
    :rtype: bool
    """
    rc = get_resource_container(context)
    if rc:
        return bool(rc.add_resource(location, resource))
    return False
