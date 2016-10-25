# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _

from shuup.category_extensions.models.populator_rules import (
    AttributePopulatorRule, CreationDatePopulatorRule,
    ManufacturerPopulatorRule
)


class AttributePopulatorRuleForm(forms.ModelForm):
    identifier = "attribute_populator"
    title = _("Automatic category: Attribute")

    class Meta:
        model = AttributePopulatorRule
        exclude = []


class ManufacturerPopulatorRuleForm(forms.ModelForm):
    identifier = "manufacturer_populator"
    title = _("Automatic category: Manufacturer")

    class Meta:
        model = ManufacturerPopulatorRule
        exclude = []


class CreationDatePopulatorRuleForm(forms.ModelForm):
    identifier = "creationdate_populator"
    title = _("Autocategory: Creation Date")

    class Meta:
        model = CreationDatePopulatorRule
        exclude = []
