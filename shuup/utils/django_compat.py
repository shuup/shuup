# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import django

try:
    from django.urls.resolvers import RegexPattern
    from django.urls import (
        clear_url_caches, get_callable, get_resolver, get_urlconf,
        NoReverseMatch, resolve, Resolver404, reverse,
        reverse_lazy, set_urlconf, URLResolver, URLPattern
    )
except ImportError:
    from django.core.urlresolvers import (  # noqa (F401)
        clear_url_caches, get_callable, get_resolver, get_urlconf,
        NoReverseMatch, RegexURLPattern as RegexPattern,
        RegexURLResolver as URLResolver, resolve, Resolver404,
        reverse, reverse_lazy, set_urlconf
    )
    URLPattern = RegexPattern


try:
    from django.utils.text import format_lazy
except ImportError:
    from django.utils.translation import string_concat as format_lazy  # noqa (F401)


try:
    from django.utils.encoding import force_bytes, force_text
except ImportError:
    from django.utils.text import force_bytes, force_text  # noqa (F401)


try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    class MiddlewareMixin(object):  # noqa (F811)
        pass


def is_anonymous(user):
    return user.is_anonymous


def is_authenticated(user):
    return user.is_authenticated


def get_middleware_classes():
    from django.conf import settings
    return (settings.MIDDLEWARE_CLASSES if django.VERSION < (2, 0) else settings.MIDDLEWARE)
