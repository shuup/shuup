# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json

import six
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Count, Manager, Q, QuerySet
from django.http.response import JsonResponse
from django.template.defaultfilters import yesno
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from shoop.admin.utils.urls import get_model_url, NoModelUrl
from shoop.utils.dates import try_parse_date
from shoop.utils.objects import compact
from shoop.utils.serialization import ExtendedJSONEncoder


def maybe_callable(thing, context=None):
    """
    If `thing` is callable, return it.
    If `thing` names a callable attribute of `context`, return it.
    """
    if callable(thing):
        return thing

    if isinstance(thing, six.string_types):
        thing = getattr(context, thing, None)
        if callable(thing):
            return thing

    return None


def maybe_call(thing, context, args=None, kwargs=None):
    """
    If `thing` is callable, call it with args and kwargs and return the value.
    If `thing` names a callable attribute of `context`, call it with args and kwargs and return the value.
    Otherwise return `thing`.
    """
    func = maybe_callable(context=context, thing=thing)
    if func:
        thing = func(*(args or ()), **(kwargs or {}))
    return thing


class Filter(object):
    type = None

    def to_json(self, context):
        return None

    def filter_queryset(self, queryset, column, value):
        return queryset  # pragma: no cover


class ChoicesFilter(Filter):
    type = "choices"

    def __init__(self, choices=None, filter_field=None):
        self.filter_field = filter_field
        self.choices = choices

    def _flatten_choices(self, context):
        if not self.choices:
            return None
        choices = maybe_call(self.choices, context=context)
        if isinstance(choices, QuerySet):
            choices = [(c.pk, c) for c in choices]
        return [(None, "")] + [
            (force_text(value, strings_only=True), force_text(display))
            for (value, display)
            in choices
        ]

    def to_json(self, context):
        return {
            "choices": self._flatten_choices(context)
        }

    def filter_queryset(self, queryset, column, value):
        return queryset.filter(**{(self.filter_field or column.id): value})


class RangeFilter(Filter):
    type = "range"

    def __init__(self, min=None, max=None, step=None, field_type=None, filter_field=None):
        """
        :param filter_field: Filter field (Django query expression). If None, column ID is used.
        :type filter_field: str|None
        :param min: Minimum value.
        :param max: Maximum value.
        :param step: Step value. See the HTML5 documentation for semantics.
        :param field_type: Field type string. See the HTML5 documentation for semantics.
        :type field_type: str|None
        """
        self.filter_field = filter_field
        self.min = min
        self.max = max
        self.step = step
        self.field_type = field_type

    def to_json(self, context):
        return {
            "range": compact({
                "min": maybe_call(self.min, context=context),
                "max": maybe_call(self.max, context=context),
                "step": maybe_call(self.step, context=context),
                "type": self.field_type,
            })
        }

    def filter_queryset(self, queryset, column, value):
        if value:
            min = value.get("min")
            max = value.get("max")
            q = {}
            filter_field = (self.filter_field or column.id)
            if min is not None:
                q["%s__gte" % filter_field] = min
            if max is not None:
                q["%s__lte" % filter_field] = max
            if q:
                queryset = queryset.filter(**q)
        return queryset


class DateRangeFilter(RangeFilter):

    def __init__(self, *args, **kwargs):
        super(DateRangeFilter, self).__init__(*args, **kwargs)
        if not self.field_type:
            self.field_type = "date"

    def filter_queryset(self, queryset, column, value):
        if value:
            value = {
                "min": try_parse_date(value.get("min")),
                "max": try_parse_date(value.get("max")),
            }
        return super(DateRangeFilter, self).filter_queryset(queryset, column, value)


class TextFilter(Filter):
    type = "text"

    def __init__(self, field_type=None, placeholder=None, operator="icontains", filter_field=None):
        """
        :param filter_field: Filter field (Django query expression). If None, column ID is used.
        :type filter_field: str|None
        :param field_type: Field type string. See the HTML5 documentation for semantics.
        :type field_type: str|None
        :param placeholder: Field placeholder string.
        :type placeholder: str|None
        :param operator: Django operator for the queryset.
        :type operator: str
        """
        self.filter_field = filter_field
        self.field_type = field_type
        self.placeholder = placeholder
        self.operator = operator

    def to_json(self, context):
        return {
            "text": compact({
                "type": self.field_type,
                "placeholder": force_text(self.placeholder) if self.placeholder else None,
            })
        }

    def filter_queryset(self, queryset, column, value):
        if value:
            value = force_text(value).strip()
            if value:
                return queryset.filter(**{"%s__%s" % ((self.filter_field or column.id), self.operator): value})
        return queryset


class MultiFieldTextFilter(TextFilter):
    def __init__(self, filter_fields, **kwargs):
        """
        :param filter_field: List of Filter fields (Django query expression).
        :type filter_field: list<str>
        :param kwargs: Kwargs for `TextFilter`.
        """
        super(MultiFieldTextFilter, self).__init__(**kwargs)
        self.filter_fields = tuple(filter_fields)

    def filter_queryset(self, queryset, column, value):
        if value:
            q = Q()
            for filter_field in self.filter_fields:
                q |= Q(**{"%s__%s" % (filter_field, self.operator): value})
            return queryset.filter(q)
        return queryset


true_or_false_filter = ChoicesFilter([
    (False, _("no")),
    (True, _("yes"))
])


class Column(object):
    def __init__(self, id, title, **kwargs):
        self.id = id
        self.title = title
        self.sort_field = kwargs.pop("sort_field", id)
        self.display = kwargs.pop("display", id)
        self.class_name = kwargs.pop("class_name", None)
        self.filter_config = kwargs.pop("filter_config", None)
        self.sortable = bool(kwargs.pop("sortable", True))
        self.linked = bool(kwargs.pop("linked", True))
        if kwargs and type(self) is Column:  # If we're not derived, validate that client code doesn't fail
            raise NameError("Unexpected kwarg(s): %s" % kwargs.keys())

    def to_json(self, context=None):
        out = {
            "id": force_text(self.id),
            "title": force_text(self.title),
            "className": force_text(self.class_name) if self.class_name else None,
            "filter": self.filter_config.to_json(context=context) if self.filter_config else None,
            "sortable": bool(self.sortable),
            "linked": bool(self.linked),
        }
        return dict((key, value) for (key, value) in six.iteritems(out) if value is not None)

    def sort_queryset(self, queryset, desc=False):
        order_by = ("-" if desc else "") + self.sort_field
        queryset = queryset.order_by(order_by)
        if self.sort_field.startswith("translations__"):
            # Ref http://archlinux.me/dusty/2010/12/07/django-dont-use-distinct-and-order_by-across-relations/
            queryset = queryset.annotate(_dummy_=Count(self.sort_field))
        return queryset

    def filter_queryset(self, queryset, value):
        if self.filter_config:
            queryset = self.filter_config.filter_queryset(queryset, self, value)
        return queryset

    def get_display_value(self, context, object):
        display_callable = maybe_callable(self.display, context=context)
        if display_callable:
            return display_callable(object)
        value = object
        for bit in self.display.split("__"):
            value = getattr(value, bit, None)

        if isinstance(value, bool):
            value = yesno(value)

        if isinstance(value, Manager):
            value = ", ".join("%s" % x for x in value.all())

        return force_text(value)


class Picotable(object):
    def __init__(self, request, columns, queryset, context):
        self.request = request
        self.columns = columns
        self.queryset = queryset
        self.context = context
        self.columns_by_id = dict((c.id, c) for c in self.columns)
        self.get_object_url = maybe_callable("get_object_url", context=self.context)
        self.get_object_abstract = maybe_callable("get_object_abstract", context=self.context)

    def process_queryset(self, query):
        queryset = self.queryset

        filters = (query.get("filters") or {})
        for column, value in six.iteritems(filters):
            column = self.columns_by_id.get(column)
            if column:
                queryset = column.filter_queryset(queryset, value)

        sort = query.get("sort")
        if sort:
            desc = (sort[0] == "-")
            column = self.columns_by_id.get(sort[1:])
            if not (column and column.sortable):
                raise ValueError("Can't sort by column %r" % sort[1:])
            queryset = column.sort_queryset(queryset, desc=desc)

        return queryset

    def get_data(self, query):
        paginator = Paginator(self.process_queryset(query), query["perPage"])
        try:
            page = paginator.page(int(query["page"]))
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        out = {
            "columns": [c.to_json(context=self.context) for c in self.columns],
            "pagination": {
                "perPage": paginator.per_page,
                "nPages": paginator.num_pages,
                "nItems": paginator.count,
                "pageNum": page.number,
            },
            "items": [self.process_item(item) for item in page],
            "itemInfo": _("Showing %(per_page)s of %(n_items)s %(verbose_name_plural)s") % {
                "per_page": min(paginator.per_page, paginator.count),
                "n_items": paginator.count,
                "verbose_name_plural": self.get_verbose_name_plural(),
            }
        }
        return out

    def process_item(self, object):
        out = {
            "_id": object.id,
            "_url": (self.get_object_url(object) if callable(self.get_object_url) else None),
        }
        for column in self.columns:
            out[column.id] = column.get_display_value(context=self.context, object=object)
        out["_abstract"] = (self.get_object_abstract(object, item=out) if callable(self.get_object_abstract) else None)
        return out

    def get_verbose_name_plural(self):
        try:
            return self.queryset.model._meta.verbose_name_plural
        except AttributeError:
            return _("objects")


class PicotableViewMixin(object):
    columns = []
    picotable_class = Picotable
    template_name = "shoop/admin/base_picotable.jinja"

    def process_picotable(self, query_json):
        pico = self.picotable_class(
            request=self.request,
            columns=self.columns,
            queryset=self.get_queryset(),
            context=self
        )
        return JsonResponse(pico.get_data(json.loads(query_json)), encoder=ExtendedJSONEncoder)

    def get(self, request, *args, **kwargs):
        query = request.GET.get("jq")
        if query:
            return self.process_picotable(query)
        return super(PicotableViewMixin, self).get(request, *args, **kwargs)

    def get_object_url(self, instance):
        try:
            return get_model_url(instance)
        except NoModelUrl:
            pass
        return None

    def get_object_abstract(self, instance, item):
        """
        Get the object abstract lines (used for mobile layouts) for this object.

        Supported keys in abstract line dicts are:

        * text (required)
        * title
        * class (CSS class name -- `header` for instance)
        * raw (boolean; whether or not the `text` is raw HTML)

        :param instance: The instance
        :param item: The item dict so far. Useful for reusing precalculated values.
        :return: Iterable of dicts to pass through to the picotable javascript
        :rtype: Iterable[dict]
        """
        return None

    def get_filter(self):
        filter_string = self.request.GET.get("filter")
        return json.loads(filter_string) if filter_string else {}
