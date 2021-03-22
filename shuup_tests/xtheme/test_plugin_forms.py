# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.forms.fields import CharField, IntegerField

from shuup.testing.utils import apply_request_middleware
from shuup.xtheme import Plugin
from shuup.xtheme.plugins.forms import TranslatableField


class SomewhatConfigurablePlugin(Plugin):
    fields = {"strength": IntegerField(min_value=0, max_value=100, initial=33)}


class UtterlyConfigurablePluginWithExceptionallyImportantFieldOrder(Plugin):
    fields = [
        ("one", IntegerField()),
        ("two", IntegerField()),
        ("three", IntegerField()),
    ]


class MultilingualPlugin(Plugin):
    fields = {"untranslated_field": CharField(label="untranslated field"), "text": TranslatableField(label="my field")}


def test_generated_plugin_form(rf):
    plugin = SomewhatConfigurablePlugin(config={"exist": True})
    form_class = plugin.get_editor_form_class()
    form = form_class(data={"strength": 10}, plugin=plugin, request=apply_request_middleware(rf.get("/")))
    assert form.is_valid()
    assert form.get_config() == {"exist": True, "strength": 10}


def test_multilingual_plugin_form(settings, rf):
    plugin = MultilingualPlugin(config={"exist": True})
    form_class = plugin.get_editor_form_class()
    form = form_class(
        data={"text_en": "foobar en", "text_*": "foobar default", "untranslated_field": "untranslated"},
        plugin=plugin,
        request=apply_request_middleware(rf.get("/")),
    )
    assert form.is_valid()
    config = form.get_config()
    assert all([form.fields.get("text_%s" % language[0], "") for language in settings.LANGUAGES])
    assert "text_*" in form.fields
    assert config["exist"] == True
    assert config["untranslated_field"] == "untranslated"
    assert config["text"] == {"en": "foobar en", "*": "foobar default"}
    assert len(form.translatable_field_names) == 1
    assert form.translatable_field_names[0] == "text"
    assert len(form.monolingual_field_names) == 1
    assert form.monolingual_field_names[0] == "untranslated_field"


def test_generated_plugin_form_field_order(rf):
    plugin = UtterlyConfigurablePluginWithExceptionallyImportantFieldOrder(config={})
    form_class = plugin.get_editor_form_class()
    form = form_class(plugin=plugin, request=apply_request_middleware(rf.get("/")))
    assert list(form.fields.keys()) == ["one", "two", "three"]
