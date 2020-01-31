# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import six
from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms.utils import flatatt


def filter_form_field_choices(field, predicate, invert=False):
    """
    Filter choices of a form field and its widget by predicate.

    The predicate may be a callable of the signature ``(pair) -> bool``
    or an iterable of allowable values.

    :param field: Form field.
    :type field: django.forms.Field
    :param predicate: Predicate.
    :type predicate: function|Iterable
    :param invert: Invert the semantics of the predicate, i.e. items matching it will be rejected.
    :type invert: bool
    :return: Nothing. The field is modified in-place.
    """

    if not callable(predicate):
        allowed_values = set(predicate)

        def predicate(pair):
            return (pair[0] in allowed_values)

    if invert:
        choices = [pair for pair in field.choices if not predicate(pair)]
    else:
        choices = [pair for pair in field.choices if predicate(pair)]

    field.choices = field.widget.choices = choices


def add_form_errors_as_messages(request, form):
    """
    Add the form's errors, if any, into the request as messages.

    :param request: Request to messagify.
    :type request: django.http.HttpRequest
    :param form: The errorful form.
    :type form: django.forms.Form
    :return: Number of messages added. May be thousands, for a very unlucky form.
    :rtype: int
    """
    n_messages = 0
    for field_name, errors in form.errors.items():
        if field_name != NON_FIELD_ERRORS:
            field_label = form[field_name].label
        else:
            field_label = ""
        for error in errors:
            messages.error(request, "%s %s" % (field_label, error))
            n_messages += 1
    return n_messages


def flatatt_filter(attrs):
    attrs = dict(
        (key, value)
        for (key, value)
        in six.iteritems(attrs)
        if key and value
    )
    return flatatt(attrs)


def get_possible_name_fields_for_model(model):
    """
    Get possible name fields for given model.

    This function yields strings of field names that
    could possible be identified as name fields for model.

    For example
    get_possible_name_fields_for_model(Coupon) yields string "code"

    :param model Class object of the model:
    :type model object:
    :return: Yield strings of possible name fields.
    :rtype: str
    """

    if hasattr(model, "name_field"):
        yield model.name_field

    for field in model._meta.local_fields:
        if field.name in ["name", "title", "username"]:
            yield field.name
    if hasattr(model, "_parler_meta"):
        for field in model._parler_meta.root_model._meta.get_fields():
            if field.name not in ("master", "id", "language_code", "description"):
                yield field.name
