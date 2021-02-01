# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

from functools import reduce

from django.db import models
from django_countries.fields import Country

from shuup.utils.django_compat import force_text

__all__ = [
    "copy_model_instance",
    "get_data_dict"
]


def get_data_dict(obj, force_text_for_value=False):
    data = {}
    for f in obj._meta.fields:
        if not isinstance(f, models.AutoField) and f not in obj._meta.parents.values():
            value = getattr(obj, f.name)
            if isinstance(value, Country):
                value = value.code
            data[f.name] = (force_text(value) if force_text_for_value else value)

    return data


def copy_model_instance(obj):
    return obj.__class__(**get_data_dict(obj))


def get_model_unique_fields(model):
    for field in model._meta.local_fields:
        if isinstance(field, models.AutoField) or field.unique:
            yield field
    tmo = getattr(model._meta, "translations_model", None)
    if tmo:
        for field in get_model_unique_fields(tmo):
            if field.name not in ("master", "id", "language_code"):
                yield field


def build_or_query(over_fields, term, operator=""):
    def add_term(query_q, field):
        return (query_q | models.Q(**{("%s%s" % (field, operator)): term}))
    return reduce(add_term, over_fields, models.Q())


class SortableMixin(models.Model):
    """ Utility mixin to add manual ordering to models"""

    ordering = models.SmallIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ['ordering']
