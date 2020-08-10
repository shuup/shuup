# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from collections import OrderedDict

import six
from django.forms import BaseFormSet


class FormInstantiationAttributeError(Exception):
    """ AttributeErrors occurring within the `forms` property are transmogrified into these. """


class FormDef(object):
    def __init__(self, name, form_class, required=True, kwargs=None):
        self.name = name
        self.form_class = form_class
        self.required = bool(required)
        self.kwargs = kwargs or {}

    def instantiate(self, prefix, group_initial=None, **extra_kwargs):
        kwargs = {"prefix": prefix}
        if not issubclass(self.form_class, BaseFormSet):
            # FormSets don't support `empty_permitted` (they'll deal with it themselves)
            kwargs["empty_permitted"] = not self.required
            if not self.required:
                # FIXME: Above would raise ValueError: The empty_permitted and
                # use_required_attribute arguments may not both be True with
                # Django 2.2.
                kwargs["use_required_attribute"] = False

        kwargs.update(self.kwargs)
        kwargs.update(extra_kwargs)
        if group_initial:
            prefix_with_dash = "%s-" % prefix
            # Only copy keys from initial that begin with this form's prefix
            new_initial = dict(
                (k[len(prefix_with_dash):], v)
                for (k, v)
                in group_initial.items()
                if k.startswith(prefix_with_dash)
            )
            # But any explicitly passed kwargs shall be copied as-is
            new_initial.update(kwargs.get("initial", {}))
            kwargs["initial"] = new_initial
        form_inst = self.form_class(**kwargs)
        form_inst._required = self.required
        return form_inst


class FormGroup(object):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None):
        self.form_defs = OrderedDict()
        self.is_bound = (data is not None or files is not None)
        self.data = data
        self.files = files
        self.prefix = prefix
        self.initial = initial

        self._forms = None
        self._errors = None
        self.cleaned_data = {}

    def add_form_def(self, name, form_class, required=True, kwargs=None):
        self.form_defs[name] = FormDef(name, form_class, required, kwargs)
        return self  # Chaining convenience

    def instantiate_forms(self):
        self._forms = OrderedDict()
        for name, form_def in six.iteritems(self.form_defs):
            if self.prefix:
                prefix = "%s_%s" % (self.prefix, name)
            else:
                prefix = name

            self._forms[name] = form_def.instantiate(
                prefix=prefix,
                data=self.data,
                files=self.files,
                group_initial=self.initial
            )

    @property
    def forms(self):
        if self._forms is None:
            try:
                self.instantiate_forms()
            except AttributeError as ae:
                # As we're in a `property`, `AttributeError`s get hidden,
                # but `instantiate_forms()` may do significant processing which might raise AttributeErrors.
                # Thus we re-raise the exception as a FormInstantiationAttributeError, which the property mechanism
                # won't hide.  Why not use `raise_from`? Because Django's technical 500 page doesn't understand chained
                # exceptions and we'd end up with an utterly useless traceback.
                import sys
                tb = sys.exc_info()[2]
                # Turns out the type argument is ignored in six's Py3 emulation of reraising if the value argument is
                # is non-None. However that might not be the case for Python 2, so just to err on the safe side of
                # caution, here's the word FormInstantiationAttributeError a few more times.
                exc = FormInstantiationAttributeError(*ae.args)
                six.reraise(FormInstantiationAttributeError, exc, tb)

        return self._forms

    def __getitem__(self, item):
        return self.forms[item]

    def full_clean(self):
        self._errors = {}
        if not self.is_bound:  # Stop further processing.
            return
        self.cleaned_data = {}
        for name, form in six.iteritems(self.forms):
            if isinstance(form, BaseFormSet):
                has_errors = bool(form.total_error_count())
            else:
                has_errors = bool(form.errors)

            if has_errors:
                self._errors[name] = form.errors
            else:
                self.cleaned_data[name] = form.cleaned_data

    @property
    def errors(self):
        "Returns an ErrorDict for the data provided for the form"
        if self._errors is None:
            self.full_clean()
        return self._errors

    def is_valid(self):
        return self.is_bound and not bool(self.errors)
