# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import unicode_literals

from django.conf import settings
from django.forms import BaseModelFormSet

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.core.models import ServiceBehaviorComponent
from shuup.utils.multilanguage_model_form import TranslatableModelForm


class BehaviorFormSet(BaseModelFormSet):
    form_class = None  # Set in initialization
    model = ServiceBehaviorComponent

    validate_min = False
    min_num = 0
    validate_max = False
    max_num = 20
    absolute_max = 20
    can_delete = True
    can_order = False
    extra = 0

    def __init__(self, *args, **kwargs):
        self.form_class = kwargs.pop("form")
        self.owner = kwargs.pop("owner")
        super(BehaviorFormSet, self).__init__(*args, **kwargs)

    def _get_actual_model(self):
        return self.form_class._meta.model

    def get_name(self):
        return getattr(self._get_actual_model(), "name", None)

    def get_queryset(self):
        return self.owner.behavior_components.instance_of(self._get_actual_model())

    def form(self, **kwargs):
        if issubclass(self.form_class, TranslatableModelForm):
            kwargs.setdefault("languages", settings.LANGUAGES)
            kwargs.setdefault("default_language", settings.PARLER_DEFAULT_LANGUAGE_CODE)
        return self.form_class(**kwargs)


class BehaviorComponentFormPart(FormPart):
    formset = BehaviorFormSet
    template_name = "shuup/admin/services/_edit_behavior_components_form.jinja"

    def __init__(self, request, form, name, owner):
        self.name = name
        self.form = form
        super(BehaviorComponentFormPart, self).__init__(request, object=owner)

    def get_form_defs(self):
        yield TemplatedFormDef(
            self.name,
            self.formset,
            self.template_name,
            required=False,
            kwargs={"form": self.form, "owner": self.object},
        )

    def form_valid(self, form):
        component_form = form.forms[self.name]
        component_form.save()
        for component in component_form.new_objects:
            self.object.behavior_components.add(component)
