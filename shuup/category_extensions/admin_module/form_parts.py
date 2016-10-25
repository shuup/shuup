# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.db.models import ManyToManyField

from shuup.admin.form_part import FormPart, TemplatedFormDef
from shuup.admin.forms.fields import Select2MultipleField
from shuup.apps.provides import get_provide_objects
from shuup.category_extensions.models.category_populator import \
    CategoryPopulator
from shuup.core.models import Attribute, Manufacturer


class AutopopulateForm(forms.Form):
    created_on_start = forms.DateTimeField()
    created_on_end = forms.DateTimeField()
    manufacturer = forms.ModelMultipleChoiceField(Manufacturer.objects.all())
    attribute_name = forms.ModelChoiceField(Attribute.objects.all())
    attribute_value_start = forms.CharField(widget=forms.Textarea())
    attribute_value_end = forms.CharField(widget=forms.Textarea())


class BaseRuleModelForm(forms.ModelForm):
    class Meta:
        exclude = []

    def __init__(self, **kwargs):
        super(BaseRuleModelForm, self).__init__(**kwargs)
        _process_fields(self, **kwargs)


def _process_fields(form, **kwargs):
    instance = kwargs.get("instance")
    model_obj = form._meta.model
    for field in model_obj._meta.get_fields(include_parents=False):
        if not isinstance(field, ManyToManyField):
            continue
        formfield = Select2MultipleField(model_obj)
        objects = (getattr(instance, field.name).all() if instance else model_obj.model.objects.none())
        formfield.required = False
        formfield.initial = objects
        formfield.widget.choices = [(obj.pk, obj.name) for obj in objects]
        form.fields[field.name] = formfield


class AutopopulateFormPart(FormPart):
    name = "autopopulate_category_form"
    formset = None
    template_name = "shuup/category_extensions/admin/edit_form.jinja"

    def get_form_defs(self):
        populator = CategoryPopulator.objects.filter(category=self.object).first()

        for form in get_provide_objects("category_populator_rule"):
            kwargs = {}
            if populator:
                matching_rule = [rule for rule in populator.rules.all() if rule.identifier == form.identifier]
                if matching_rule:
                    kwargs["instance"] = matching_rule[0]

            yield TemplatedFormDef(
                form.identifier,
                form,
                self.template_name,
                required=False,
                kwargs=kwargs,
            )

    def form_valid(self, form):
        populator, created = CategoryPopulator.objects.get_or_create(category=self.object)
        populator.rules.clear()

        for provided_form in get_provide_objects("category_populator_rule"):
            rule_form = form[provided_form.identifier]
            if rule_form.changed_data:
                rule = rule_form.save()
                populator.rules.add(rule)
