# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import NoReverseMatch, reverse
from jinja2 import contextfunction

from shuup.core.models import Category, Product


@contextfunction
def model_url(context, model, absolute=False):
    uri = None
    if isinstance(model, Product):
        uri = reverse("shuup:product", kwargs=dict(pk=model.pk, slug=model.slug))

    if isinstance(model, Category):
        uri = reverse("shuup:category", kwargs=dict(pk=model.pk, slug=model.slug))

    if hasattr(model, "pk") and model.pk and hasattr(model, "url"):
        uri = "/%s" % model.url

    if not uri:  # pragma: no cover
        raise ValueError("Unable to figure out `model_url` for %r" % model)

    if absolute:
        request = context.get("request")
        if not request:  # pragma: no cover
            raise ValueError("Unable to use `absolute=True` when request does not exist")
        uri = request.build_absolute_uri(uri)
    return uri


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
