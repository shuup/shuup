# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six


class ModelCachingDescriptor(object):
    def __init__(self, name, queryset):
        self.name = name
        self.id_name = "_%s_id" % name
        self.object_name = "_%s_cache" % name
        self.queryset = queryset
        self.id_property = property(self.get_id, self.set_id)
        self.object_property = property(self.get_object, self.set_object)

    def _clear(self, instance):
        setattr(instance, self.id_name, None)
        setattr(instance, self.object_name, None)

    def set_id(self, instance, value):
        if not value:
            self._clear(instance)
        elif isinstance(value, six.integer_types):
            setattr(instance, self.id_name, value)
            current_cached = self._get_cached_object(instance)
            if current_cached and current_cached.pk != self.get_id(instance):
                setattr(instance, self.object_name, None)
        else:
            raise TypeError("Can't assign ID %r in a ModelCachingDescriptor(%s)" % (value, self.name))

    def get_id(self, instance):
        return getattr(instance, self.id_name, None)

    def set_object(self, instance, value):
        if not value:
            self._clear(instance)
        elif isinstance(value, self.queryset.model):
            if not value.pk:
                raise ValueError("Can't assign unsaved model %r in a ModelCachingDescriptor(%s)" % (value, self.name))
            setattr(instance, self.id_name, value.pk)
            setattr(instance, self.object_name, value)
        else:
            raise TypeError("Can't assign object %r in a ModelCachingDescriptor(%s)" % (value, self.name))

    def get_object(self, instance):
        if not self.get_id(instance):
            return None
        value = self._get_cached_object(instance)
        if value is None:
            value = self._cache_object(instance)
        return value

    def _cache_object(self, instance):
        object = self.queryset.get(pk=self.get_id(instance))
        setattr(instance, self.object_name, object)
        setattr(instance, self.id_name, object.pk)
        return object

    def _get_cached_object(self, instance):
        return getattr(instance, self.object_name, None)
