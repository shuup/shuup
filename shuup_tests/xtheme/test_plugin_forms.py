# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.forms.fields import IntegerField

from shuup.xtheme import Plugin
from shuup.xtheme.plugins.forms import TranslatableField


class SomewhatConfigurablePlugin(Plugin):
    fields = {
        "strength": IntegerField(min_value=0, max_value=100, initial=33)
    }

class UtterlyConfigurablePluginWithExceptionallyImportantFieldOrder(Plugin):
    fields = [
        ("one", IntegerField()),
        ("two", IntegerField()),
        ("three", IntegerField()),
    ]


def test_generated_plugin_form():
    plugin = SomewhatConfigurablePlugin(config={"exist": True})
    form_class = plugin.get_editor_form_class()
    form = form_class(data={"strength": 10}, plugin=plugin)
    assert form.is_valid()
    assert form.get_config() == {"exist": True, "strength": 10}


def test_generated_plugin_form_field_order():
    plugin = UtterlyConfigurablePluginWithExceptionallyImportantFieldOrder(config={})
    form_class = plugin.get_editor_form_class()
    form = form_class(plugin=plugin)
    assert list(form.fields.keys()) == ["one", "two", "three"]


def test_translatable_field_attrs():
    """
    Make sure attributes are passed to widgets
    """
    field = TranslatableField(attrs={"class": "passable"})
    assert field.widget.attrs.get("class") == "passable"
