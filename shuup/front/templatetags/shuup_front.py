# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from django.utils.encoding import force_text
from django.utils.functional import SimpleLazyObject
from django.utils.lru_cache import lru_cache
from django.utils.safestring import mark_safe
from django_jinja import library
from markdown import Markdown

from shuup.apps.provides import get_provide_objects


class HelpersNamespace(object):
    pass


def _get_helpers():
    helpers = HelpersNamespace()
    from shuup.front.template_helpers import general, product, category, urls

    helpers.general = general
    helpers.product = product
    helpers.category = category
    helpers.urls = urls
    for namespace in get_provide_objects("front_template_helper_namespace"):
        if namespace and getattr(namespace, "name", None):
            if callable(namespace):  # If it's a class, instantiate it
                namespace = namespace()
            setattr(helpers, namespace.name, namespace)
    return helpers


library.global_function(name="shuup", fn=SimpleLazyObject(_get_helpers))


@lru_cache()
def _cached_markdown(str_value):

    return Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.nl2br',
    ], output_format="html5").convert(str_value)


@library.filter(name="markdown")
def markdown(value):
    return mark_safe(_cached_markdown(force_text(value)))


@library.filter(name="replace_field_attrs")
def replace_field_attrs(field, **attrs):
    for attr, value in attrs.items():
        setattr(field.field, attr, value)
    return field
