# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import NoReverseMatch, reverse
from jinja2 import contextfunction

from shuup.apps.provides import get_provide_objects


@contextfunction
def model_url(context, model, absolute=False, raise_when_not_found=True, **kwargs):
    """
    Iterate over all `front_model_url_resolver` provides trying to find
    some url for the given `model`. The first value returned by the resolver
    will be used.

    If no url is returned and `raise_when_not_found` is set to True (the default),
    an exception will be raised.
    """
    front_model_url_resolvers = get_provide_objects("front_model_url_resolver")

    for resolver in front_model_url_resolvers:
        url = resolver(context, model, absolute, **kwargs)
        if url:
            return url

    if raise_when_not_found:
        # no url found
        raise ValueError("Unable to figure out `model_url` for %r" % model)


def get_url(url, *args, **kwargs):
    """
    Try to get the reversed URL for the given route name, args and kwargs.

    If reverse resolution fails, returns None (instead of throwing an exception).

    :param url: URL name.
    :type url: str
    :param args: URL args
    :type args: Iterable[object]
    :param kwargs: URL kwargs
    :type kwargs: dict[str, object]
    :return: Reversed URL or None
    :rtype: str|None
    """
    try:
        return reverse(url, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return None


def has_url(url, *args, **kwargs):
    """
    Try to get the reversed URL for the given route name, args and kwargs and return a success flag.

    :param url: URL name.
    :type url: str
    :param args: URL args
    :type args: Iterable[object]
    :param kwargs: URL kwargs
    :type kwargs: dict[str, object]
    :return: Success flag
    :rtype: bool
    """
    return bool(get_url(url, *args, **kwargs))
