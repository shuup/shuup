# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import with_statement

from django.core.urlresolvers import reverse

from shuup.core.models import Category, Product


def model_url(context, model, absolute=False, **kwargs):
    uri = None

    if isinstance(model, Product):
        uri = reverse("shuup:product", kwargs=dict(pk=model.pk, slug=model.slug))

    if isinstance(model, Category):
        uri = reverse("shuup:category", kwargs=dict(pk=model.pk, slug=model.slug))

    if hasattr(model, "pk") and model.pk and hasattr(model, "url"):
        uri = "/%s" % model.url

    if absolute:
        request = context.get("request")
        if not request:  # pragma: no cover
            raise ValueError("Error! Unable to use `absolute=True` when request does not exist.")
        uri = request.build_absolute_uri(uri)

    return uri
