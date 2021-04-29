# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.forms import BaseFormSet
from itertools import chain

from shuup.utils.form_group import FormGroup


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

    if isinstance(form, FormGroup):
        data = {}
        for subform in form.forms.values():
            data.update(get_form_data(subform, prepared=prepared))
        return data

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
        else:
            value = form.initial.get(name, field.initial)
            if callable(value):
                value = value()

        if prepared:
            value = field.prepare_value(value)
            if value is None:
                continue
        data[prefixed_name] = value
    return data
