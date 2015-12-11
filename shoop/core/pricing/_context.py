# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import abc
import hashlib

import six
from django.http import HttpRequest
from django.utils.encoding import force_bytes
from django.utils.timezone import now


class PricingContextable(six.with_metaclass(abc.ABCMeta)):
    """
    Object that is or can be converted to a pricing context.

    Currently there exists two kind of `PricingContextable` objects:
    `PricingContext`(and its subclasses) and `HttpRequest`.

    .. note::

       Expression ``isinstance(request, PricingContextable)`` will
       return True for a ``request`` which is `HttpRequest`, because
       `HttpRequest` is registered as a subclass of this abstract base
       class.

    This abstract base class is just a helper to allow writing simpler
    type specifiers, since we want to allow passing `HttpRequest` as a
    pricing context even though it is not a `PricingContext`.
    """
    pass
PricingContextable.register(HttpRequest)


class PricingContext(PricingContextable):
    """
    Context for pricing.
    """
    REQUIRED_VALUES = ()

    def __init__(self, **kwargs):
        kwargs.setdefault("time", now())
        for name, value in kwargs.items():
            setattr(self, name, value)
        for name in self.REQUIRED_VALUES:
            if not hasattr(self, name):
                raise ValueError("%s is a required value for %s but is not set." % (name, self))

    def get_cache_key_parts(self):
        return [getattr(self, key) for key in self.REQUIRED_VALUES]

    def get_cache_key(self):
        parts_text = "\n".join(force_bytes(part) for part in self.get_cache_key_parts())
        return "%s_%s" % (
            self.__class__.__name__,
            hashlib.sha1(parts_text).hexdigest()
        )

    cache_key = property(get_cache_key)
