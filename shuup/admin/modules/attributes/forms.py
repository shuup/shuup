# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.forms import BaseModelFormSet

from shuup.core.models import Attribute, AttributeChoiceOption, AttributeType
from shuup.utils.multilanguage_model_form import MultiLanguageModelForm, TranslatableModelForm


class AttributeForm(MultiLanguageModelForm):
    class Meta:
        model = Attribute
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()

        # when it is not a choice attribute, make sure the min/max are zero
        if data["type"] != AttributeType.CHOICES:
            data["min_choices"] = 0
            data["max_choices"] = 0

        return data


class AttributeChoiceOptionForm(MultiLanguageModelForm):
    class Meta:
        model = AttributeChoiceOption
        fields = ("name",)

    def __init__(self, *args, **kwargs):
        self.attribute = kwargs.pop("attribute")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.attribute = self.attribute
        super().save(commit)


class AttributeChoiceOptionFormSet(BaseModelFormSet):
    model = AttributeChoiceOption
    form_class = AttributeChoiceOptionForm

    validate_min = False
    min_num = 0
    validate_max = False
    max_num = 100
    absolute_max = 100
    can_delete = True
    can_order = False
    extra = 0

    def __init__(self, **kwargs):
        self.attribute = kwargs.pop("attribute")
        self.languages = kwargs.pop("languages")
        self.request = kwargs.pop("request")
        super().__init__(**kwargs)

    def form(self, **kwargs):
        kwargs.setdefault("attribute", self.attribute)
        kwargs.setdefault("request", self.request)
        if issubclass(self.form_class, TranslatableModelForm):
            kwargs.setdefault("languages", settings.LANGUAGES)
            kwargs.setdefault("default_language", settings.PARLER_DEFAULT_LANGUAGE_CODE)
        return self.form_class(**kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(attribute=self.attribute)
