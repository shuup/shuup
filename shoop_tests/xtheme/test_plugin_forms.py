# -*- coding: utf-8 -*-
from django.forms.fields import IntegerField

from shoop.xtheme import Plugin
from shoop.xtheme.plugins.forms import TranslatableField


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
