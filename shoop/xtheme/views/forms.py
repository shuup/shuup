# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django import forms
from django.utils.translation import ugettext_lazy as _
from shoop.utils.form_group import FormGroup
from shoop.xtheme.layout import LayoutCell
from shoop.xtheme.plugins.base import Plugin


class LayoutCellGeneralInfoForm(forms.Form):
    plugin = forms.ChoiceField(label=_("Plugin"), required=False)

    def __init__(self, **kwargs):
        self.layout_cell = kwargs.pop("layout_cell")
        super(LayoutCellGeneralInfoForm, self).__init__(**kwargs)
        self.populate()

    def populate(self):
        """
        Populate the form with fields for size and plugin selection.
        """
        sizes = ["sm", "md"]  # TODO: Parametrize? Currently Bootstrap dependent.
        sizes.extend(set(self.layout_cell.sizes) - set(sizes))
        self.sizes = sizes
        for size in self.sizes:
            self.fields["size_%s" % size] = forms.IntegerField(
                label=size.upper(),
                required=False,
                min_value=0,
                max_value=12,  # TODO: Parametrize? Currently Bootstrap dependent.
                initial=self.layout_cell.sizes.get(size)
            )
        plugin_choices = Plugin.get_plugin_choices(empty_label=_("No Plugin"))
        plugin_field = self.fields["plugin"]
        plugin_field.choices = plugin_field.widget.choices = plugin_choices
        plugin_field.initial = self.layout_cell.plugin_identifier

    def save(self):
        """
        Save size configuration. Plugin configuration is done via JavaScript POST.
        """
        data = self.cleaned_data
        for size in self.sizes:
            self.layout_cell.sizes[size] = data["size_%s" % size]


class LayoutCellFormGroup(FormGroup):
    """
    Form group containing the LayoutCellGeneralInfoForm and a possible plugin-dependent configuration form.
    """
    def __init__(self, **kwargs):
        self.layout_cell = kwargs.pop("layout_cell")
        assert isinstance(self.layout_cell, LayoutCell)
        super(LayoutCellFormGroup, self).__init__(**kwargs)
        self.add_form_def("general", LayoutCellGeneralInfoForm, kwargs={
            "layout_cell": self.layout_cell
        })
        plugin = self.layout_cell.instantiate_plugin()
        if plugin:
            form_class = plugin.get_editor_form_class()
            if form_class:
                self.add_form_def("plugin", form_class, kwargs={"plugin": plugin})

    def save(self):
        self.forms["general"].save()
        plugin_form = self.forms.get("plugin")
        if plugin_form:
            self.layout_cell.config = plugin_form.get_config()
