# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import os

import six
from django.conf import settings
from django_jinja import library
from easy_thumbnails.alias import aliases
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.templatetags.thumbnail import RE_SIZE


def process_thumbnailer_options(kwargs):
    default_options = getattr(settings, "THUMBNAIL_DEFAULT_OPTIONS", {})
    options = {}
    options.update(default_options)
    options.update(kwargs)
    size = options.setdefault('size', (128, 128))
    if isinstance(size, six.text_type):
        m = RE_SIZE.match(size)
        if m:
            options["size"] = (int(m.group(1)), int(m.group(2)))
        else:
            raise ValueError("%r is not a valid size." % size)
    return options


@library.filter
def thumbnail(source, alias=None, generate=True, **kwargs):
    if not source:
        return None
    thumbnailer = get_thumbnailer(source)
    if not thumbnailer:
        return None

    if _is_svg(thumbnailer):
        return source.url if hasattr(source, 'url') else None

    if alias:
        options = aliases.get(alias, target=thumbnailer.alias_target)
        options.update(process_thumbnailer_options(kwargs))
    else:
        options = process_thumbnailer_options(kwargs)

    try:
        thumbnail = thumbnailer.get_thumbnail(options, generate=generate)
        return thumbnail.url
    except (IOError, InvalidImageFormatError):
        return None


def _is_svg(thumbnailer):
    file_name = getattr(thumbnailer, "name", None)
    if not file_name:
        return False
    return bool(os.path.splitext(file_name)[1].lower() == ".svg")


@library.filter
def thumbnailer(source):
    return get_thumbnailer(source)
