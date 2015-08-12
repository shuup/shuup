# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from itertools import chain
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet


def get_form_data(form, prepared=False):
    """
    Get the current form data; with `prepared`, in a format that can
    be directly passed back as `data` to a form to simulate form submissions.

    :param form: A form.
    :type form: django.forms.BaseForm|django.forms.BaseFormSet
    :param prepared: Prepare the values?
    :type prepared: bool
    :return: Dict of data
    :rtype: dict
    """

    # This is based on Django's `django.forms.forms.BaseForm::changed_data` method.

    if isinstance(form, BaseFormSet):
        data = {}
        for subform in chain([form.management_form], form.forms):
            data.update(get_form_data(subform, prepared=prepared))
        return data

    data = {}
    for name, field in form.fields.items():
        prefixed_name = form.add_prefix(name)
        data_value = field.widget.value_from_datadict(form.data, form.files, prefixed_name)

        if data_value:
            value = data_value
            data[prefixed_name] = value
        else:
            if not field.show_hidden_initial:
                initial_value = form.initial.get(name, field.initial)
                if callable(initial_value):
                    initial_value = initial_value()
            else:
                initial_prefixed_name = form.add_initial_prefix(name)
                hidden_widget = field.hidden_widget()
                try:
                    initial_value = field.to_python(hidden_widget.value_from_datadict(
                        form.data, form.files, initial_prefixed_name))
                except ValidationError:
                    form._changed_data.append(name)
                    continue
            value = initial_value
        if prepared:
            value = field.prepare_value(value)
        data[prefixed_name] = value
    return data

