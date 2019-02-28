# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import hashlib

import six
from django.core.urlresolvers import reverse
from django.utils.encoding import force_bytes, force_text
from django.utils.translation import override


class AdminModule(object):
    name = "_Base_"

    # A menu entry to represent this module in breadcrumbs
    breadcrumbs_menu_entry = None

    def get_urls(self):
        """
        :rtype: list[django.core.urlresolvers.RegexURLPattern]
        """
        return ()

    def get_menu_category_icons(self):
        """
        :rtype: dict[str,str]
        """
        return {}

    def get_menu_entries(self, request):
        """
        :rtype: list[shuup.admin.base.MenuEntry]
        """
        return ()

    def get_search_results(self, request, query):
        """
        :rtype: list[shuup.admin.base.SearchResult]
        """
        return ()

    def get_dashboard_blocks(self, request):
        """
        :rtype: list[shuup.admin.dashboard.DashboardBlock]
        """
        return ()

    def get_help_blocks(self, request, kind):
        """
        :param request: Request
        :type request: django.http.request.HttpRequest
        :param kind: block kind. Currently "setup" or "quicklink"
        :type kind: str
        :rtype: list[shuup.admin.views.home.HelpBlock]
        """
        return ()

    def get_required_permissions(self):
        """
        :rtype: list[str]
        """
        with override(language="en"):
            return ("%s" % self.name,)

    def get_extra_permissions(self):
        """
        Define custom extra permissions for admin module for option
        to limit certain parts of the admin module based on per user
        permission string. Should return unique list permission strings
        across the installation to prevent unwanted side effects.

        :rtype: list[str]
        """
        return ()

    def get_notifications(self, request):
        """
        :rtype: list[shuup.admin.base.Notification]
        """
        return ()

    def get_activity(self, request, cutoff):
        """
        :param cutoff: Cutoff datetime
        :type cutoff: datetime.datetime
        :param request: Request
        :type request: django.http.request.HttpRequest
        :return: list[shuup.admin.base.Activity]
        """
        return ()

    def get_model_url(self, object, kind, shop=None):
        """
        Retrieve an admin URL for the given object of the kind `kind`.

        A falsy value must be returned if the module does not know
        how to reverse the given object.

        :param object: A object instance (or object class).
        :type object: django.db.models.Model
        :param kind: URL kind. Currently "detail", "list" or "new".
        :type kind: str
        :param shop: The shop that owns the resource
        :type shop: shuup.core.models.Shop|None
        :return: The reversed URL or none.
        :rtype: str|None
        """
        return None


class Resolvable(object):
    _url = ""  # Set on instance level.

    @property
    def url(self):
        """
        Resolve this object's `_url` to an actual URL.

        :return: URL or no URL.
        :rtype: str|None
        """
        url = self._url
        if not url:
            return None

        if isinstance(url, tuple):
            (viewname, args, kwargs) = url
            return reverse(viewname, args=args, kwargs=kwargs)

        if isinstance(url, six.string_types):
            if url.startswith("http") or "/" in url:
                return url
            return reverse(url)

        raise TypeError("Can't real_url: %r" % url)

    @property
    def original_url(self):
        return self._url


class MenuEntry(Resolvable):
    def __init__(self, text, url, icon=None, category=None, subcategory=None, ordering=99999, aliases=()):
        self.text = text
        self._url = url
        self.icon = icon
        self.category = category
        self.subcategory = subcategory
        self.ordering = ordering
        self.aliases = tuple(aliases)

    def get_search_query_texts(self):
        yield self.text
        for alias in self.aliases:
            yield alias


class SearchResult(Resolvable):
    def __init__(self, text, url, icon=None, category=None, is_action=False, relevance=100, target=None):
        self.text = text
        self._url = url
        self.icon = icon
        self.category = category
        self.is_action = bool(is_action)
        self.relevance = relevance
        self.target = target

    def to_json(self):
        return {
            "text": force_text(self.text),
            "url": self.url,
            "icon": self.icon,
            "category": force_text(self.category),
            "isAction": self.is_action,
            "relevance": self.relevance,
            "target": self.target,
        }


class Notification(Resolvable):
    KINDS = ("info", "success", "warning", "danger")

    def __init__(self, text, title=None, url=None, kind="info", dismissal_url=None, datetime=None):
        """
        :param text: The notification's text.
        :type text: str
        :param title: An optional title for the notification.
        :type title: str|None
        :param url: The optional main URL for the notification.
        :type url: str|None
        :param kind: The kind of the notification (see KINDS)
        :type kind: str
        :param dismissal_url: An optional dismissal URL for the notification.
                              The admin framework will add a button that will
                              cause an AJAX post into this URL.
        :type dismissal_url: str|None
        :param datetime: An optional date+time for this notification.
        :type datetime: datetime
        """
        self.title = title
        self.text = text
        self._url = url
        self.dismissal_url = dismissal_url
        self.kind = kind
        self.datetime = datetime
        bits = [force_text(v) for (k, v) in sorted(vars(self).items())]
        self.id = hashlib.md5(force_bytes("+".join(bits))).hexdigest()


class Activity(Resolvable):
    def __init__(self, datetime, text, url=None):
        self.datetime = datetime
        self.text = text
        self._url = url


class Section(object):
    """
    Subclass this and add the class to the admin_*_section provide list
    (e.g. `admin_order_section`) to show a custom section on the specified
    model object's admin detail page.

    `identifier` must be unique
    `name` the section caption
    `icon` the section icon
    `template` the section template file
    `extra_js` the section extra javascript template file,
               set a file which contains js code inside a <script> tag
    `order` the order
    """
    identifier = ""
    name = ""
    icon = ""
    template = ""
    extra_js = ""
    order = 0

    @classmethod
    def visible_for_object(cls, obj, request=None):
        """
        Returns whether this sections must be visible for the provided object (e.g. `order`)
        :type model object: e.g. shuup.core.models.Order
        :type request: HttpRequest
        :return whether this section must be shown in order section list, defaults to false
        :rtype: bool
        """
        return False

    @classmethod
    def get_context_data(cls, obj, request=None):
        """
        Returns additional information to be used in the template

        To fetch this data in the template, you must first add it to your request's context

        e.g. `context[admin_order_section.identifier] =
                admin_order_section.get_context_data(self.object)`


        :type object: e.g. shuup.core.models.Order
        :type request: HttpRequest
        :return additional context data
        :rtype: object|None
        """
        return None
