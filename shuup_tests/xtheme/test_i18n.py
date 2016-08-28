# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms

from shuup.xtheme.plugins.forms import TranslatableField
from shuup_tests.utils import printable_gibberish


class Form(forms.Form):
    field = TranslatableField(languages=("en", "fi"))


def test_translatable_field_initial():
    dummy = printable_gibberish()
    tf = Form()
    assert str(tf).count(dummy) == 0
    tf = Form(initial={"field": dummy})
    assert str(tf).count(dummy) == 1  # Should only exist in the untranslated field
    tf = Form(initial={"field": {"en": dummy, "fi": dummy}})
    assert str(tf).count(dummy) == 2  # Should exist in two fields


def test_translatable_field_data():
    dummy = printable_gibberish()
    tf = Form(data={"field_en": dummy, "field_fi": dummy, "field_*": "oops"})
    assert str(tf).count(dummy) == 2
    assert str(tf).count("oops") == 1
    tf.full_clean()
    assert tf.cleaned_data["field"] == {"en": dummy, "fi": dummy, "*": "oops"}
    tf = Form(data={"field_en": dummy})
    assert str(tf).count(dummy) == 1
    tf.full_clean()
    assert tf.cleaned_data["field"] == {"en": dummy}
