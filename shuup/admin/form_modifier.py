# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import abc
import six
from django.contrib import messages
from django.db.transaction import atomic

from shuup.apps.provides import get_provide_objects
from shuup.utils.excs import Problem


class FormModifier(six.with_metaclass(abc.ABCMeta)):
    def get_extra_fields(self, object=None):
        """
        Extra fields for creation view.

        :param object: Object linked to form.
        :type object: django.db.models.Model
        :return: List of extra fields that should be added to form.
        Tuple should contain field name and Django form field.
        :rtype: list[(str,django.forms.Field)]
        """
        pass

    def clean_hook(self, form):
        """
        Extra clean for creation form.

        This hook will be called in `~Django.forms.Form.clean` method of
        the form, after calling parent clean.  Implementor of this hook
        may call `~Django.forms.Form.add_error` to add errors to form or
        modify the ``form.cleaned_data`` dictionary.

        :param form: Form that is currently cleaned.
        :type form: django.forms.Form
        :rtype: None
        """
        pass

    def form_valid_hook(self, form, object):
        """
        Extra form valid handler for creation view.

        :param form: Form that is currently handled.
        :type form: django.forms.Form
        :param object: object linked to form.
        :type object: django.db.models.Model
        :rtype: None
        """
        pass


class ModifiableFormMixin(object):
    form_modifier_provide_key = None

    def clean(self):
        cleaned_data = super(ModifiableFormMixin, self).clean()
        for extend_class in get_provide_objects(self.form_modifier_provide_key):
            extend_class().clean_hook(self)
        return cleaned_data


class ModifiableViewMixin(object):
    def add_extra_fields(self, form, object=None):
        for extend_class in get_provide_objects(form.form_modifier_provide_key):
            for field_key, field in extend_class().get_extra_fields(object) or []:
                form.fields[field_key] = field

    def get_form(self, form_class=None):
        form = super(ModifiableViewMixin, self).get_form(self.form_class)
        self.add_extra_fields(form, self.object)
        return form

    def form_valid_hook(self, form, object):
        has_extension_errors = False
        for extend_class in get_provide_objects(form.form_modifier_provide_key):
            try:
                extend_class().form_valid_hook(form, object)
            except Problem as problem:
                has_extension_errors = True
                messages.error(self.request, problem)
        return has_extension_errors

    @atomic
    def form_valid(self, form):
        response = super(ModifiableViewMixin, self).form_valid(form)
        has_extension_errors = self.form_valid_hook(form, self.object)

        if has_extension_errors:
            return self.form_invalid(form)
        else:
            return response
