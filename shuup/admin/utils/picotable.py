# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import datetime
import json

import six
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Manager, Q, QuerySet
from django.http.response import HttpResponse, JsonResponse
from django.template.defaultfilters import yesno
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from filer.models import Image

from shuup.admin.utils.urls import get_model_url, NoModelUrl
from shuup.apps.provides import get_provide_objects
from shuup.core.models import ProductMedia
from shuup.utils.dates import try_parse_datetime
from shuup.utils.i18n import format_money, get_locally_formatted_datetime
from shuup.utils.importing import load
from shuup.utils.money import Money
from shuup.utils.objects import compact
from shuup.utils.serialization import ExtendedJSONEncoder


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
    If `thing` is callable, call it with `args` and `kwargs` and return the value.
    If `thing` names a callable attribute of `context`, call it with args and kwargs and return the value.
    Otherwise return `thing`.
    """
    func = maybe_callable(context=context, thing=thing)
    if func:
        thing = func(*(args or ()), **(kwargs or {}))
    return thing


class Filter(object):
    type = None
    filter_field = None

    def get_filter_field(self, column, context):
        if self.filter_field:
            return self.filter_field
        if column.context and not maybe_callable(column.display, context=context):
            return column.display
        return column.id

    def to_json(self, context):
        return None

    def filter_queryset(self, queryset, column, value, context):
        return queryset  # pragma: no cover


class ChoicesFilter(Filter):
    type = "choices"

    def __init__(self, choices=None, filter_field=None, default=None):
        self.filter_field = filter_field
        self.choices = choices
        self.default = default

    def _flatten_choices(self, context):
        if not self.choices:
            return None
        choices = maybe_call(self.choices, context=context)
        if isinstance(choices, QuerySet):
            choices = [(c.pk, c) for c in choices]
        return [("_all", "---------")] + [
            (force_text(value, strings_only=True), force_text(display))
            for (value, display)
            in choices
        ]

    def to_json(self, context):
        choices = self._flatten_choices(context)
        default_choice = self.default
        if default_choice is None and choices:
            default_choice = choices[0][0]
        return {
            "choices": choices,
            "defaultChoice": default_choice
        }

    def filter_queryset(self, queryset, column, value, context):
        if value == "_all":
            return queryset
        filter_field = self.get_filter_field(column, context)
        return queryset.filter(**{filter_field: value})


class Select2Filter(ChoicesFilter):
    type = "select2"

    def to_json(self, context):
        json_dict = super(Select2Filter, self).to_json(context)
        json_dict["select2"] = True
        return json_dict


class MPTTFilter(Select2Filter):
    type = "mptt"

    def filter_queryset(self, queryset, column, value, context):
        qs = super(MPTTFilter, self).filter_queryset(queryset, column, value, context)
        return qs.get_descendants(include_self=True)


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

    def filter_queryset(self, queryset, column, value, context):
        if value:
            min = value.get("min")
            max = value.get("max")

            # strip string values
            if type(max) in six.string_types:
                max = max.strip()
            if type(min) in six.string_types:
                min = min.strip()

            q = {}
            filter_field = self.get_filter_field(column, context)
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

    def filter_queryset(self, queryset, column, value, context):
        if value:
            value = {
                "min": try_parse_datetime(value.get("min")),
                "max": try_parse_datetime(value.get("max"))
            }
        return super(DateRangeFilter, self).filter_queryset(queryset, column, value, context)


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

    def filter_queryset(self, queryset, column, value, context):
        if value:
            value = force_text(value).strip()
            field = self.get_filter_field(column, context)
            if value:
                return queryset.filter(**{"%s__%s" % (field, self.operator): value})
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

    def filter_queryset(self, queryset, column, value, context):
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
        self.display = kwargs.pop("display", id)
        self.class_name = kwargs.pop("class_name", None)
        self.filter_config = kwargs.pop("filter_config", None)
        self.sortable = bool(kwargs.pop("sortable", True))
        self.linked = bool(kwargs.pop("linked", True))
        self.raw = bool(kwargs.pop("raw", False))
        self.ordering = kwargs.pop("ordering", 9999)
        self.context = None  # will be set after initializing
        self.sort_field = kwargs.pop("sort_field", None)
        self.allow_highlight = kwargs.pop("allow_highlight", True)

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
            "allowHighlight": bool(self.allow_highlight),
            "raw": bool(self.raw),
        }
        return dict((key, value) for (key, value) in six.iteritems(out) if value is not None)

    def get_sort_field(self, sort_field):
        if self.sort_field:
            return self.sort_field
        if self.filter_config and self.filter_config.filter_field:
            return self.filter_config.filter_field
        if self.display and not maybe_callable(self.display, context=self.context):
            return self.display
        return self.id

    def set_sort_field(self):
        self.sort_field = self.get_sort_field(None)

    def set_context(self, context):
        self.context = context
        self.set_sort_field()

    def sort_queryset(self, queryset, desc=False):
        order_by = ("-" if desc else "") + self.sort_field
        return queryset.order_by(order_by)

    def filter_queryset(self, queryset, value):
        if self.filter_config:
            queryset = self.filter_config.filter_queryset(queryset, self, value, self.context)
        return queryset

    def get_display_value(self, context, object):
        # Look for callable from view context
        display_callable = maybe_callable(self.display, context=context)
        if display_callable:
            return display_callable(object)

        # Look for callable from provided column objects contexts
        display_callable = self.search_from_provided_contexts(object)
        if display_callable:
            return display_callable(object)

        value = object
        for bit in self.display.split("__"):
            value = getattr(value, bit, None)

        return_value = self.check_different_types(value)
        if return_value is not None:
            return return_value

        if not value:
            value = ""

        return force_text(value)

    def check_different_types(self, value):
        if isinstance(value, ProductMedia):
            return "<img src='/media/%s'>" % value.get_thumbnail()

        if isinstance(value, Image):
            thumbnailer = get_thumbnailer(value)
            options = {"size": (64, 64)}
            thumbnail = thumbnailer.get_thumbnail(options, generate=True)
            return "<img src='%s'>" % thumbnail.url

        if isinstance(value, bool):
            value = yesno(value)

        if isinstance(value, Manager):
            value = ", ".join("%s" % x for x in value.all())
            return value

        if isinstance(value, datetime.datetime):
            return get_locally_formatted_datetime(value)

        if isinstance(value, Money):
            return escape(format_money(value))

    def search_from_provided_contexts(self, object):
        provide_object_key = "provided_columns_%s" % type(object).__name__
        for provided_column_object in get_provide_objects(provide_object_key):
            obj = provided_column_object()
            display_callable = maybe_callable(self.display, context=obj)
            if display_callable:
                return display_callable(object)

    def __repr__(self):
        return "<Column: %s> %s" % (self.title, self.id)


class Picotable(object):
    def __init__(self, request, columns, mass_actions, queryset, context):
        for column in columns:
            column.set_context(context)
        self.request = request
        self.columns = columns
        self.mass_actions = mass_actions
        self.queryset = queryset
        self.context = context
        self.columns_by_id = dict((c.id, c) for c in self.columns)
        self.get_object_url = maybe_callable("get_object_url", context=self.context)
        self.get_object_abstract = maybe_callable("get_object_abstract", context=self.context)
        self.get_object_extra = maybe_callable("get_object_extra", context=self.context)
        self.default_filters = self._get_default_filters()

    def _get_default_filter(self, column):
        filter_config = getattr(column, "filter_config")
        if(filter_config and hasattr(filter_config, "default") and filter_config.default is not None):
            field = filter_config.filter_field or column.id
            return (field, filter_config.default)
        else:
            return None

    def _get_default_filters(self):
        filters = {}
        for column in self.columns:
            default_filter = self._get_default_filter(column)
            if default_filter:
                filters[default_filter[0]] = default_filter[1]
        return filters

    def process_queryset(self, query):
        queryset = self.queryset
        ordered = getattr(self.queryset, "ordered", None)
        if ordered is not None and not ordered:
            queryset = self.queryset.order_by("-id")

        filters = (query.get("filters") or self._get_default_filters())
        for column, value in six.iteritems(filters):
            column = self.columns_by_id.get(column)
            if column:
                queryset = column.filter_queryset(queryset, value)

        sort = query.get("sort")
        if sort:
            desc = (sort[0] == "-")
            column = self.columns_by_id.get(sort[1:])
            if not (column and column.sortable):
                raise ValueError("Error! Can't sort by column %r." % sort[1:])
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
            "massActions": self.mass_actions,
            "items": [self.process_item(item) for item in page],
            "itemInfo": _("Showing %(per_page)s of %(n_items)s %(verbose_name_plural)s") % {
                "per_page": min(paginator.per_page, paginator.count),
                "n_items": paginator.count,
                "verbose_name_plural": self.get_verbose_name_plural(),
            }
        }
        return out

    def process_item(self, object):
        object_url = self.get_object_url(object) if callable(self.get_object_url) else None
        object_extra = self.get_object_extra(object) if callable(self.get_object_extra) else None
        out = {
            "_id": object.id,
            "_url": object_url,
            "_linked_in_mobile": True if object_url else False,
            "_extra": object_extra
        }
        for column in self.columns:
            out[column.id] = column.get_display_value(context=self.context, object=object)
        out["type"] = type(object).__name__
        out["_abstract"] = (self.get_object_abstract(object, item=out) if callable(self.get_object_abstract) else None)
        return out

    def get_verbose_name_plural(self):
        try:
            return self.queryset.model._meta.verbose_name_plural
        except AttributeError:
            return _("objects")


class PicotableViewMixin(object):
    url_identifier = None
    default_columns = []
    columns = []
    mass_actions = []
    picotable_class = Picotable
    related_objects = []
    template_name = "shuup/admin/base_picotable.jinja"
    toolbar_buttons_provider_key = None
    mass_actions_provider_key = None

    def process_picotable(self, query_json):
        mass_actions = self.load_mass_actions()
        pico = self.picotable_class(
            request=self.request,
            columns=self.columns,
            mass_actions=mass_actions,
            queryset=self.get_queryset(),
            context=self
        )
        return JsonResponse(pico.get_data(json.loads(query_json)), encoder=ExtendedJSONEncoder)

    def get(self, request, *args, **kwargs):
        query = request.GET.get("jq")
        if query:
            return self.process_picotable(query)
        return super(PicotableViewMixin, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Post action is where Mass Actions post their data.
        """
        data = request.body.decode("utf-8")
        data = json.loads(data)
        action_identifier = data.get("action", None)
        ids = data.get("values", [])

        mass_action = self._get_mass_action(action_identifier)
        if mass_action is None:
            return JsonResponse({"error": force_text(_("Mass Action encountered an unknown error."))})
        if isinstance(mass_action, PicotableFileMassAction):
            return mass_action.process(request, ids)

        mass_action.process(request, ids)
        return JsonResponse({"ok": True})

    def _get_mass_actions(self):
        mass_actions = self.mass_actions[:]  # copy

        # add mass actions from the view mass action provider
        if getattr(self, "mass_actions_provider_key", None):
            for mass_action_provider in get_provide_objects(self.mass_actions_provider_key):
                mass_actions.extend(list(mass_action_provider.get_mass_actions_for_view(self)))

        # add mass actions from the global mass action provider
        for mass_action_provider in get_provide_objects("admin_mass_actions_provider"):
            mass_actions.extend(list(mass_action_provider.get_mass_actions_for_view(self)))

        return mass_actions

    def _get_mass_action(self, action_identifier):
        for mass_action in self._get_mass_actions():
            loaded_action = load(mass_action)()
            if loaded_action.identifier == action_identifier:
                return loaded_action
        return None

    def get_object_url(self, instance):
        try:
            return get_model_url(instance, user=self.request.user, shop=self.request.shop)
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

        :param instance: The instance.
        :param item: The item dict so far. Useful for reusing precalculated values.
        :return: Iterable of dicts to pass through to the picotable javascript.
        :rtype: Iterable[dict]
        """
        return None

    def get_object_extra(self, instance):
        """
        Returns extra information as a dictionary for each object.

        The following special keys are used in picotable:

        * class - add the class list (space separated) to each row/item class list

        :rtype: None|dict
        """
        return None

    def get_filter(self):
        filter_string = self.request.GET.get("filter")
        return json.loads(filter_string) if filter_string else {}

    def load_mass_actions(self):
        actions = []
        for action in self._get_mass_actions():
            obj = load(action)()
            action_data = {}
            extra_data = obj.get_action_info(self.request)

            if extra_data and isinstance(extra_data, dict):
                action_data.update(extra_data)

            action_data.update({
                "key": obj.identifier,
                "value": obj.label
            })
            actions.append(action_data)
        return actions


class PicotableMassAction(object):
    """
    Simple Mass Action.

    This action only processes the given id's in subclass.

    Examples:
    * `shuup.admin.modules.orders.mass_actions.CancelOrderAction`
    * `shuup.admin.modules.products.mass_actions.VisibleMassAction`
    """
    label = _("Mass Action")
    identifier = "mass_action"

    def __repr__(self):
        return "Mass Action: %s" % force_text(self.label)

    def process(self, request, ids):
        """
        Process the given ids in masses.

        :param request: `WSGIRequest`
        :param ids: list of ids.
        :return: None
        """
        pass

    def get_action_info(self, request):
        """
        Returns a dict with additional action data to be rendered
        in html action option element as data-xxx attribute.

        :param request: `WSGIRequest`
        :return dict: dictionary with extra info to be rendered in option element.
        """
        return {}


class PicotableMassActionProvider(object):
    @classmethod
    def get_mass_actions_for_view(cls, view):
        """
        Returns a list of mass actions for a given `view`.

        :param view: `django.views.View`
        :return list[PicotableMassAction]: list of picotable mass actions definition (strings).
        """
        return []


class PicotableFileMassAction(PicotableMassAction):
    """
    File Mass Action.

    This action returns file as a response.

    Examples:
    * `shuup.admin.modules.orders.mass_actions.OrderConfirmationPdfAction`
    * `shuup.admin.modules.products.mass_actions.FileResponseAction`
    """
    def process(self, request, ids):
        """
        Process and return `HttpResponse`.

        Example:
            response = HttpResponse(content_type="text/csv")
            response['Content-Disposition'] = 'attachment; filename="mass_action.csv"'
            writer = csv.writer(response)
            writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
            return response

        :param request: `WSGIRequest`
        :param ids: list of ids.
        :return: `HttpResponse`
        """
        pass


class PicotableRedirectMassAction(PicotableMassAction):
    """
    Redirect Mass Action.

    This view saves selected id's into session which are then
    further processed in the mass action view.

    Redirect of this view is handled in `picotable.js`.

    To use this action, your admin module must supply admin_url
    and a view for the action.

    Examples:
    * `shuup.admin.modules.contacts.mass_actions.EditContactsAction`
    * `shuup.admin.modules.products.mass_actions.EditProductAttributesAction`
    """
    redirect_url = None

    def process(self, request, ids):
        request.session["mass_action_ids"] = ids
        return HttpResponse("ok")

    def get_action_info(self, request):
        if self.redirect_url:
            return {
                "redirects": True,
                "redirect_url": self.redirect_url
            }

        return {}


class PicotableJavascriptMassAction(PicotableMassAction):
    """
    Javascript Mass Action.

    This view saves invokes a pre-defined javascript function
    with the list of object ids.

    Set the function call in `callback`, e.g. `deleteProducts`.
    The mass action will then invoce the callback as `deleteProducts(ids)`
    """
    callback = None

    def get_action_info(self, request):
        return {
            "callback": self.callback
        }
