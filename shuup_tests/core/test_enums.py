# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.db import models
from enumfields import Enum, EnumIntegerField


class Color(Enum):
    RED = 0
    GREEN = 1

    class Labels:
        RED = "red"
        GREEN = "green"


class Colored(models.Model):
    color = EnumIntegerField(Color, default=Color.RED)

    class Meta:
        app_label = "colored_test"


class ColoredForm(forms.ModelForm):
    class Meta:
        model = Colored
        fields = ["color"]


def test_form_enum_field_choices():
    choices = ColoredForm.base_fields["color"].choices
    assert choices == [(0, "red"), (1, "green")]
