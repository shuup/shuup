# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import itertools
from operator import ior

import django
import six
from django.db.models import ForeignKey, Q
from parler.models import TranslatableModel

from shuup.importer.utils import get_model_possible_name_fields
from shuup.utils.models import get_model_unique_fields

NotCached = object()


class RelatedMapper(object):
    def __init__(self, handler, row_session, field):
        self.row_session = row_session
        self.handler = handler
        self.field = field
        if django.VERSION < (2, 0):
            self.rel = rel = field.rel
            self.to = to = rel.to
        else:
            self.rel = rel = field.remote_field
            self.to = to = rel.model
        self.map_cache = {}
        self.fk_cache = {}
        self.explicit_uk_fields = tuple(handler._meta.fk_matchers.get(field.name) or ())
        self.is_translated = hasattr(self.to, "_parler_meta")
        self.translated_fields = self.to._parler_meta.root_model._meta.get_fields() if self.is_translated else []
        self.translated_field_names = [f.name for f in self.translated_fields]

        uk_fields = dict((f.name, f) for f in get_model_unique_fields(to))
        uk_fields.update((fname, None) for fname in self.explicit_uk_fields)

        # TODO: can explicit fields be used to map stuff
        uk_fields.update((f.name, f) for f in get_model_possible_name_fields(to))

        self.uk_fields = uk_fields
        self.reverse_fields = list(itertools.chain(
            self.explicit_uk_fields,
            [f for f in uk_fields if f not in ("id", "pk")],
            ["pk"]
        ))
        manager = to.objects
        if issubclass(to, TranslatableModel):
            manager = manager.language(handler.language)

        self.manager = manager

    def make_q(self, arg, skip_pk=False):
        qs = []
        for name, field in six.iteritems(self.uk_fields):
            if skip_pk and name in ("id", "pk"):
                continue
            if field:
                try:
                    arg = field.get_prep_value(arg)
                except Exception:
                    continue
                if self.is_translated and name in self.translated_field_names:
                    name = "translations__%s" % name
                qs.append(Q(**{name: arg}))
        try:
            int(arg)
            qs.append(Q(pk=arg))
        except Exception:
            pass

        if not qs:
            return Q()
        return six.moves.reduce(ior, qs)

    def map_multi_value(self, value):
        if value is None:
            return None
        if value in self.map_cache:
            return self.map_cache[value]

        split_value = self.split_value(value)
        values_mapped = set()
        for s_value in split_value:
            mapped = self.map_single_value(s_value)
            if mapped:
                values_mapped.add(mapped)

        self.map_cache[value] = values_mapped
        return values_mapped

    def map_single_value(self, value):
        if isinstance(value, six.string_types):
            value = value.strip()

        if not value:
            return None
        value = "%s" % value
        mapped = self.fk_cache.get(value, NotCached)
        if mapped is NotCached:
            try:
                mapped = self._get_existing_value(mapped, value)
            except (IndexError, self.to.DoesNotExist, ValueError):
                mapped = self._create_new_object(mapped, value)

        self.fk_cache[value] = mapped
        return mapped

    def _create_new_object(self, mapped, value):  # noqa (C901)
        obj = self.to()

        if self.is_translated:
            obj.set_current_language(self.handler.language)
            for field in self.translated_fields:
                if field.name not in ("master", "id", "language_code", "description"):
                    setattr(obj, field.name, value)

        for field in obj._meta.local_fields:
            if (
                django.VERSION < (2, 0) and
                isinstance(field, ForeignKey) and
                isinstance(self.row_session.instance, field.rel.to)
            ):
                setattr(obj, field.name, self.row_session.instance)
            elif (
                django.VERSION > (2, 0) and
                isinstance(field, ForeignKey) and
                isinstance(self.row_session.instance, field.remote_field.model)
            ):
                setattr(obj, field.name, self.row_session.instance)
            elif field.name in ("name", "title"):
                setattr(obj, field.name, value)

            elif field.name == "shop":
                obj.shop = self.row_session.shop

        # ask the handler whether we can create new objects of this type
        if not self.handler.can_create_object(obj):
            return None

        try:
            obj.save()
            mapped = obj
        except ValueError:
            # something went wrong
            # try to save it after the main item has been saved
            self.row_session.post_save_objects.append(obj)
            mapped = obj
        return mapped

    def _get_existing_value(self, mapped, value):
        if value.startswith("#"):
            mapped = self.manager.get(pk=int(value[1:]))
        else:
            q = self.make_q(value, skip_pk=True)
            mapped = self.manager.filter(q).first()
            if not mapped:
                mapped = self.manager.get(pk=value)
        return mapped

    def map_instances(self, instances):
        return [self.map_instance(instance) for instance in instances]

    def map_instance(self, instance):
        if not instance:
            return None
        field = self.reverse_fields[0]
        value = getattr(instance, field)
        if field in ("pk", "id"):
            value = "#%s" % value
        return value

    def split_value(self, value):
        if isinstance(value, (list, tuple)):
            return tuple(value)
        if not isinstance(value, six.string_types):
            return [value]

        likely_splitters = (";", "|", "\n", ",")
        split_value = [value]
        for splitter in likely_splitters:
            if splitter in value:
                split_value = value.split(splitter)
                break
        return split_value
