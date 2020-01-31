# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

"""
"Tagged JSON" encoder/decoder.

Objects that are normally not unambiguously representable via JSON
are encoded into special objects of the form `{tag: val}`; the encoding
and decoding process can be customized however necessary.
"""

from __future__ import unicode_literals

import datetime
import decimal
from enum import Enum

import django.utils.dateparse as dateparse
from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from jsonfield.encoder import JSONEncoder
from six import text_type

from shuup.utils.importing import load
from shuup.utils.iterables import first


def isoformat(obj):
    return obj.isoformat()


def encode_enum(enum_val):
    enum_cls = enum_val.__class__
    spec = "%s:%s" % (enum_cls.__module__, enum_cls.__name__)
    try:
        if load(spec) != enum_cls:
            raise ImproperlyConfigured("Error! That's not the same class.")
    except ImproperlyConfigured:  # Also raised by `load`
        return enum_val.value  # Fall back to the bare value.
    return [spec, enum_val.value]


def decode_enum(val):
    spec, value = val
    cls = load(spec)
    if issubclass(cls, Enum):
        return cls(value)
    return value  # Fall back to the bare value. Not optimal, I know.


class TagRegistry(object):
    def __init__(self):
        self.tags = {}

    def register(self, tag, classes, encoder=text_type, decoder=None):
        if decoder is None:
            if isinstance(classes, (list, tuple)):
                decoder = classes[0]
            else:
                decoder = classes
        if not callable(decoder):
            raise ValueError("Error! Decoder `%r` for tag `%r` is not callable." % (decoder, tag))
        if not callable(encoder):
            raise ValueError("Error! Encoder `%r` for tag `%r` is not callable." % (encoder, tag))

        self.tags[tag] = {
            "classes": classes,
            "encoder": encoder,
            "decoder": decoder
        }

    def encode(self, obj, default):
        for tag, info in six.iteritems(self.tags):
            if isinstance(obj, info["classes"]):
                return {tag: info["encoder"](obj)}
        return default(obj)

    def decode(self, obj):
        if len(obj) == 1:
            tag, val = first(obj.items())
            info = self.tags.get(tag)
            if info:
                return info["decoder"](val)
        return obj


#: The default tag registry.
tag_registry = TagRegistry()
tag_registry.register("$datetime", datetime.datetime, encoder=isoformat, decoder=dateparse.parse_datetime)
tag_registry.register("$date", datetime.date, encoder=isoformat, decoder=dateparse.parse_date)
tag_registry.register("$time", datetime.time, encoder=isoformat, decoder=dateparse.parse_time)
tag_registry.register("$dec", decimal.Decimal)
tag_registry.register("$enum", Enum, encoder=encode_enum, decoder=decode_enum)


class TaggedJSONEncoder(JSONEncoder):
    registry = tag_registry

    def default(self, obj):
        return self.registry.encode(obj, super(JSONEncoder, self).default)
