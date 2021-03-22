# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.forms.formsets import DELETION_FIELD_NAME, BaseFormSet


class ProductChildBaseFormSet(BaseFormSet):
    deletion_label = None

    def __init__(self, **kwargs):
        kwargs.pop("empty_permitted", None)
        self.request = kwargs.pop("request", None)

        super(ProductChildBaseFormSet, self).__init__(**kwargs)

    def _construct_form(self, i, **kwargs):
        form = super(ProductChildBaseFormSet, self)._construct_form(i, **kwargs)
        form.fields[DELETION_FIELD_NAME].label = self.deletion_label
        return form
