# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import copy
from collections import OrderedDict, defaultdict
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from shuup.notify.admin_module.utils import get_name_map
from shuup.notify.enums import UNILINGUAL_TEMPLATE_LANGUAGE, TemplateUse
from shuup.notify.models import Script
from shuup.utils.i18n import get_language_name


class ScriptForm(forms.ModelForm):
    event_identifier = forms.ChoiceField(label=_("Event"), help_text=_("Choose which event to bind this script to."))
    name = forms.CharField(label=_("Script Name"), help_text=_("Type in a descriptive name for your new script."))
    enabled = forms.BooleanField(
        label=_("Enable Script"),
        help_text=_("Choose whether this script should be activated when its event fires."),
        required=False,
    )

    class Meta:
        model = Script
        fields = ("event_identifier", "name", "enabled")

    def __init__(self, **kwargs):
        self.shop = kwargs.pop("shop", None)
        super(ScriptForm, self).__init__(**kwargs)
        event_choices = get_name_map("notify_event")
        self.fields["event_identifier"].choices = event_choices
        self.fields["event_identifier"].widget.choices = event_choices
        if self.instance.pk:
            self.fields["event_identifier"].help_text = _(
                "Warning! Changing the event for an existing script may have unexpected effects."
            )

    def save(self, commit=True):
        self.instance.shop = self.shop
        return super(ScriptForm, self).save(commit)


class ScriptItemEditForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.script_item = kwargs.pop("script_item")
        self.event_class = kwargs.pop("event_class")
        super(ScriptItemEditForm, self).__init__(*args, **kwargs)
        self.variables = self.event_class.variables.copy()
        self.populate_form()

    def populate_form(self):
        self.binding_field_info = OrderedDict()
        self.template_field_info = defaultdict(OrderedDict)
        self.template_languages = []

        for identifier, binding in sorted(self.script_item.bindings.items(), key=lambda ib: ib[1].position):
            self._populate_binding_fields(identifier, binding)

        self._populate_template_fields()

    def _populate_template_fields(self):
        template_use = getattr(self.script_item, "template_use", TemplateUse.NONE)
        if template_use == TemplateUse.MULTILINGUAL:
            self.template_languages = []
            # TODO: Should we get this list from somewhere else?
            for language_code, language_name in settings.LANGUAGES:
                self.template_languages.append((language_code, get_language_name(language_code)))
        elif template_use == TemplateUse.UNILINGUAL:
            self.template_languages = [(UNILINGUAL_TEMPLATE_LANGUAGE, _("Template"))]
        else:  # Nothing to do
            return

        fields = self.script_item.template_fields.items()
        for lang_code, lang_name in self.template_languages:
            for t_field_name, base_field in fields:
                field = copy.deepcopy(base_field)
                field.label = "%s (%s)" % (field.label, lang_name)

                if lang_code == settings.PARLER_DEFAULT_LANGUAGE_CODE:  # Only default language is required
                    field.required = getattr(base_field, "required", False)
                else:
                    field.required = False
                field_name = "t_%s_%s" % (lang_code, t_field_name)
                self.fields[field_name] = field
                self.template_field_info[lang_code][t_field_name] = field_name

    def _populate_binding_fields(self, binding_identifier, binding):
        """
        :param binding_identifier: Binding identifier.
        :type binding_identifier: str
        :param binding: Binding object.
        :type binding: Binding
        """
        binding_field_info = self.binding_field_info.setdefault(binding_identifier, {"binding": binding})
        if binding.allow_constant:
            field_name = "b_%s_c" % binding_identifier
            self.fields[field_name] = binding.type.get_field(
                label="Constant", required=(binding.required and not binding.allow_variable), initial=binding.default
            )
            binding_field_info["constant"] = field_name

        if binding.allow_variable:
            variables = [
                (var_identifier, var.name)
                for (var_identifier, var) in self.variables.items()
                if binding.accepts_any_type or binding.type.is_coercible_from(var.type)
            ]
            if variables:
                choices = [("", "---------")] + variables
                field_name = "b_%s_v" % binding_identifier
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    label=_("Bind to Variable"),
                    required=(binding.required and not binding.allow_constant),
                )
                binding_field_info["variable"] = field_name
                # TODO: Maybe show a disabled field instead of nothing?

    def get_initial(self):
        initial = {}
        for identifier, binding in self.script_item.bindings.items():
            bind_data = self.script_item.data.get(identifier, {})
            field_info = self.binding_field_info.get(identifier)
            if not field_info:
                return
            for f in ("constant", "variable"):
                if field_info.get(f):
                    initial[field_info[f]] = bind_data.get(f)

        template_data = self.script_item.data.get("template_data", {})
        for lang_code, field_info in self.template_field_info.items():
            lang_templates = template_data.get(lang_code, {})
            for t_field_name, field_name in field_info.items():
                if lang_templates.get(t_field_name):
                    initial[field_name] = lang_templates.get(t_field_name)

        return initial

    def _save_binding(self, new_data, identifier, binding):  # noqa (C901)
        field_info = self.binding_field_info.get(identifier)
        if not field_info:
            return

        if binding.allow_variable and "variable" in field_info:
            variable_name = self.cleaned_data.get(field_info["variable"])
            if variable_name:
                new_data[identifier] = {"variable": variable_name}
                return

        if binding.allow_constant and "constant" in field_info:
            constant_value = self.cleaned_data.get(field_info["constant"])
            if constant_value:
                if hasattr(constant_value, "value"):  # Might be an enum TODO: fixme
                    constant_value = constant_value.value
                if hasattr(constant_value, "pk"):  # Might be a model instance TODO: fixme
                    constant_value = constant_value.pk
                new_data[identifier] = {"constant": constant_value}
                return

        if binding.required:
            message = "Error! Binding %s is required, but has no value." % binding.name
            if field_info.get("constant"):
                self.add_error(field_info["constant"], message)
            if field_info.get("variable"):
                self.add_error(field_info["variable"], message)

    def _save_bindings(self, new_data):
        for identifier, binding in self.script_item.bindings.items():
            self._save_binding(new_data, identifier, binding)

    def _save_template(self, new_data):
        template_data = {}

        for lang_code, field_info in self.template_field_info.items():
            t_field_name_to_field_name = dict(field_info.items())
            lang_vals = dict(
                (t_field_name, (self.cleaned_data.get(field_name) or "").strip())
                for (t_field_name, field_name) in field_info.items()
            )
            if not any(lang_vals.values()):  # Not worth saving
                continue
            can_save = True

            if lang_code == settings.PARLER_DEFAULT_LANGUAGE_CODE:
                for t_field_name, content in lang_vals.items():
                    actual_field_name = t_field_name_to_field_name[t_field_name]
                    if self.fields[actual_field_name].required and not content:  # Add error only to default languages
                        self.add_error(field_info[t_field_name], _("This field is missing content."))
                        can_save = False

            if can_save:
                template_data[lang_code] = lang_vals
        new_data["template_data"] = template_data

    def save(self):
        new_data = {}
        self._save_bindings(new_data)
        self._save_template(new_data)
        if self.errors:
            raise forms.ValidationError("Error! There are errors.")
        self.script_item.data = new_data
        return self.script_item
