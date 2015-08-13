# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.core.urlresolvers import NoReverseMatch, reverse
from jinja2 import contextfunction

from shoop.core.models import Product


@contextfunction
def model_url(context, model, absolute=False):
    uri = None
    if isinstance(model, Product):
        uri = reverse("shoop:product", kwargs=dict(pk=model.pk, slug=model.slug))

    if not uri:  # pragma: no cover
        raise ValueError("Unable to figure out `model_url` for %r" % model)

    if absolute:
        request = context.get("request")
        if not request:  # pragma: no cover
            raise ValueError("Unable to use `absolute=True` when request does not exist")
        uri = request.build_absolute_uri(uri)
    return uri


def has_url(url, *args, **kwargs):
    try:
        reverse(url, args=args, kwargs=kwargs)
        return True
    except NoReverseMatch:
        return False
