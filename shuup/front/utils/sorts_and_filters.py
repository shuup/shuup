# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import abc
from collections import OrderedDict

import six
from django import forms
from django.conf import settings
from django.db.models import Q
from django.forms import (
    ChoiceField, ModelChoiceField, ModelMultipleChoiceField,
    MultipleChoiceField
)

from shuup import configuration
from shuup.apps.provides import get_provide_objects
from shuup.core import cache
from shuup.core.utils import context_cache
from shuup.xtheme import get_theme_cache_key

FACETED_DEFAULT_CONF_KEY = "front_faceted_configurations"
FACETED_CATEGORY_CONF_KEY_PREFIX = "front_faceted_category_configurations_%s"
FORM_MODIFIER_PROVIDER_KEY = "front_extend_product_list_form"


class ProductListFormModifier(six.with_metaclass(abc.ABCMeta)):

    """
    Interface class for modifying product lists

    This interface can be used to sort and filter product lists in
    category and search view.

    By subclassing this interface the ProductListForm fields can be
    added. Also this interface provides methods for sorting and
    filtering product lists.
    """

    def should_use(self, configuration):
        """
        :param configuration: current configurations
        :type configuration: dict
        :return: Boolean whether the modifier should be used based
        on current configurations.
        :rtype: boolean
        """
        return False

    def get_ordering(self, configuration):
        """
        :param configuration: current configurations
        :type configuration: dict
        :return: Ordering value based on configurations
        :rtype: int
        """
        pass

    def get_fields(self, request, category=None):
        """
        Extra fields for product list form.

        :param request: Current request
        :param category: Current category
        :type category: shuup.core.models.Category|None
        :return: List of extra fields that should be added to form.
        Tuple should contain field name and Django form field.
        :rtype: list[(str,django.forms.Field)]
        """
        pass

    def get_choices_for_fields(self):
        """
        Provide sort choices for product list form

        :return: List of sort choices that should be added for form
        sort field. Tuple should contain sort key and label name.
        :rtype: list[(str,str)]
        """
        pass

    def sort_products(self, request, products, data):
        """
        Sort products in case sort choices is provided

        Sort products in cse the list should be sorted based on
        sort choice provided by this class.

        :param request: Current request
        :param products: Products to sort
        :type products: list[shuup.code.models.Product]
        :param data: product list form data
        :type data: dict
        :return: List of products that might be sorted
        :rtype: list[shuup.code.models.Product]
        """
        return products

    def get_filters(self, request, data):
        """
        Get filters based for the product list view

        Add Django query filters for Product queryset based
        on current request and ProductListForm data.

        :param request: current request
        :param data: Data from ProductListForm
        :type data: dict
        :return: Django query filter that can be used to
        filter Product queryset.
        :rtype: django.db.models.Q`
        """
        pass

    def get_queryset(self, queryset, data):
        """
        Modify product queryset

        Modify current queryset and return the new one. This
        can be used when there is need for stacking multiple
        filters for one queryset.

        :return: Updated product queryset
        :rtype: Product.queryset
        """
        pass

    def filter_products(self, request, products, data):
        """
        Filter product objects

        Filtering products list based on current request and
        ProductListForm data.

        :param request:
        :param products: List of products
        :rtype products: list[shuup.core.models.Product]
        :param data: Data from ProductListForm
        :type data: dict
        :return: Filtered product list
        :rtype: list[shuup.core.models.Product]
        """
        return products

    def get_admin_fields(self):
        """
        Admin fields for sorts and filters configurations

        Adds fields for sorts and filters admin configuration
        form.

        :return: List of fields that should be added to form.
        Tuple should contain field name and Django form field.
        :rtype: list[(str,django.forms.Field)]
        """
        pass

    def clean_hook(self, form):
        """
        Extra clean for product list form.

        This hook will be called in `~Django.forms.Form.clean` method of
        the form, after calling parent clean.  Implementor of this hook
        may call `~Django.forms.Form.add_error` to add errors to form or
        modify the ``form.cleaned_data`` dictionary.

        :param form: Form that is currently cleaned
        :type form: ProductListForm
        :rtype: None
        """
        pass


class ProductListForm(forms.Form):

    def __init__(self, request, shop, category, *args, **kwargs):
        super(ProductListForm, self).__init__(*args, **kwargs)
        for extend_obj in _get_active_modifiers(shop, category):
            for field_key, field in extend_obj.get_fields(request, category) or []:
                is_choice_field = isinstance(field, (
                    ModelMultipleChoiceField, ModelChoiceField, ChoiceField, MultipleChoiceField
                ))
                has_choices = (is_choice_field and len(field.choices))

                if field_key not in self.fields:
                    if is_choice_field and has_choices:
                        self.fields[field_key] = field
                    elif not is_choice_field:
                        self.fields[field_key] = field

            for field_key, choices in extend_obj.get_choices_for_fields() or []:
                if field_key in self.fields:
                    self.fields[field_key].widget.choices += choices

    def clean(self):
        cleaned_data = super(ProductListForm, self).clean()
        for extend_class in get_provide_objects(FORM_MODIFIER_PROVIDER_KEY):
            extend_class().clean_hook(self)
        return cleaned_data


def get_configuration(shop=None, category=None, force_category_override=False):
    default_configuration = configuration.get(
        shop, FACETED_DEFAULT_CONF_KEY, settings.SHUUP_FRONT_DEFAULT_SORT_CONFIGURATION)

    category_config = configuration.get(None, _get_category_configuration_key(category))
    # when override_default_configuration is True, we override the default configuration
    if category_config and (category_config.get("override_default_configuration") or force_category_override):
        return category_config

    return default_configuration


def set_configuration(shop=None, category=None, data=None):
    if category and category.pk:
        configuration.set(None, _get_category_configuration_key(category), data)
    elif shop:
        configuration.set(shop, FACETED_DEFAULT_CONF_KEY, data)
        cache.bump_version(get_theme_cache_key(shop))

    # clear active keys
    context_cache.bump_cache_for_item(category)
    if not category:
        from shuup.core.models import Category
        for cat_pk in Category.objects.all().values_list("pk", flat=True):
            context_cache.bump_cache_for_pk(Category, cat_pk)


def get_query_filters(request, category, data):
    filter_q = Q()
    for extend_obj in _get_active_modifiers(request.shop, category):
        extra_filter = extend_obj.get_filters(request, data)
        if extra_filter:
            filter_q &= extra_filter
    return filter_q


def post_filter_products(request, category, products, data):
    for extend_obj in _get_active_modifiers(request.shop, category):
        products = extend_obj.filter_products(request, products, data)
    return products


def sort_products(request, category, products, data):
    for extend_obj in _get_active_modifiers(request.shop, category):
        products = extend_obj.sort_products(request, products, data)
    return products


def bump_product_queryset_cache():
    context_cache.bump_cache_for_item("product_queryset")


def get_product_queryset(queryset, request, category, data):
    # pass the request and category down to the `get_queryset` method
    queryset_data = data.copy()
    queryset_data.update({
        "request": request,
        "category": category
    })
    for extend_obj in _get_active_modifiers(request.shop, category):
        new_queryset = extend_obj.get_queryset(queryset, queryset_data)
        if new_queryset is not None:
            queryset = new_queryset
    return queryset


def cached_product_queryset(queryset, request, category, data):
    """
    Returns the cached queryset or cache it when needed
    Note: this method returns a list of Product instances
    rtype: list[Product]
    """
    key_data = OrderedDict()
    for k, v in data.items():
        if isinstance(v, list):
            v = "|".join(v)
        key_data[k] = v

    item = "product_queryset:"

    if request.customer.is_all_seeing:
        item = "%sU%s" % (item, request.user.pk)
    if category:
        item = "%sC%s" % (item, category.pk)

    key, products = context_cache.get_cached_value(
        identifier="product_queryset",
        item=item,
        allow_cache=True,
        context=request,
        data=key_data
    )

    if products is not None:
        return products

    products = list(queryset)
    context_cache.set_cached_value(key, products)
    return products


def _get_category_configuration_key(category):
    return (FACETED_CATEGORY_CONF_KEY_PREFIX % category.pk if category and category.pk else None)


def _get_active_modifiers(shop=None, category=None):
    key = None
    if category:
        key, val = context_cache.get_cached_value(
            identifier="active_modifiers", item=category, allow_cache=True, context={"shop": shop})
        if val is not None:
            return val

    configurations = get_configuration(shop=shop, category=category)

    def sorter(extend_obj):
        return extend_obj.get_ordering(configurations)

    objs = []
    for cls in get_provide_objects(FORM_MODIFIER_PROVIDER_KEY):
        obj = cls()
        if obj.should_use(configurations):
            objs.append(obj)

    sorted_objects = sorted(objs, key=sorter)
    if category and key:
        context_cache.set_cached_value(key, sorted_objects)
    return sorted_objects


def get_form_field_label(identifier, default):
    return settings.SHUUP_FRONT_OVERRIDE_SORTS_AND_FILTERS_LABELS_LOGIC.get(identifier, default)
