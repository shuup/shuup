# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.contrib.auth import get_user_model
from django.utils import translation
from django.utils.encoding import force_text

from shuup.admin.utils.bs3_renderers import AdminFieldRenderer

User = get_user_model()


def test_field_title_quoting():
    with translation.override("en"):
        field = forms.ModelMultipleChoiceField(queryset=User.objects.all(), help_text='Something about "Control"')
        field.choices = []  # Don't bother with database stuff
        assert '"Control"' in force_text(field.help_text)
        form = forms.Form()
        form.fields["field1"] = field
        form.fields["field2"] = forms.CharField(label="An Unrelated Field")
        assert "&quot;Control&quot;" in force_text(AdminFieldRenderer(form["field1"]).render())
        assert 'title=""' not in force_text(AdminFieldRenderer(form["field2"]).render())
