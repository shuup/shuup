# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text


class RelaxedModelChoiceField(forms.ModelChoiceField):
    # `RelaxedModelChoiceField`s allow manually setting `choices` with full validation
    # as an improvement over the normal `ModelChoiceField`.
    def to_python(self, value):
        try:
            return super(RelaxedModelChoiceField, self).to_python(value)
        except ValidationError as verr:
            if verr.code == "invalid_choice":
                # If the original code declared this as invalid, see if we have custom choices.
                if hasattr(self, "_choices"):
                    # Stringly [sic] typed comparison...
                    value = force_text(value)
                    key = self.to_field_name or 'pk'
                    for (pk, obj) in self._choices:
                        if force_text(pk) == value or force_text(getattr(obj, key, '')) == value:
                            if obj is None or isinstance(obj, self.queryset.model):
                                return obj
            raise verr  # Just reraise the original exception then, but from here for clarity
