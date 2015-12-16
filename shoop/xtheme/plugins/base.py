# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

from shoop.apps.provides import (
    get_identifier_to_object_map, get_provide_objects
)
from shoop.utils.text import space_case
from shoop.xtheme.plugins.forms import GenericPluginForm

SENTINEL = object()


class Plugin(object):
    """
    A plugin that can be instantiated within a `shoop.xtheme.layout.LayoutCell`.

    Other plugins should inherit from this class and register themselves in the
    `xtheme_plugin` provide category.
    """
    identifier = None
    fields = []
    required_context_variables = set()
    name = _("Plugin")  # User-visible name
    editor_form_class = GenericPluginForm

    def __init__(self, config):
        """
        Instantiate a Plugin with the given `config` dictionary.

        :param config: Dictionary of freeform configuration data
        :type config: dict
        """
        self.config = config

    def is_context_valid(self, context):
        """
        Check that the given rendering context is valid for rendering this plugin.

        By default, just checks `required_context_variables`.

        :param context: Rendering context
        :type context: jinja2.runtime.Context
        :return: True if we should bother trying to render this
        :rtype: bool
        """
        for key in self.required_context_variables:
            if context.get(key, SENTINEL) is SENTINEL:
                return False
        return True

    def render(self, context):
        """
        Return the HTML for a plugin in a given rendering context.

        :param context: Rendering context
        :type context: jinja2.runtime.Context
        :return: String of rendered content.
        :rtype: str
        """
        return ""  # pragma: no cover

    def get_editor_form_class(self):
        """
        Return the form class for editing this plugin.

        The form class should either derive from PluginForm, or at least have a `get_config()` method.

        Form classes without `fields` are treated the same way as if you'd return `None`,
        i.e. no configuration form is presented to the user.

        :return: Editor form class
        :rtype: class[forms.Form]|None
        """
        # Could be overridden in suitably special subclasses.
        if self.fields:
            return self.editor_form_class

    @classmethod
    def load(cls, identifier):
        """
        Get a plugin class based on the identifier from the `xtheme_plugin` provides registry.

        :param identifier: Plugin class identifier
        :type identifier: str
        :return: A plugin class, or None
        :rtype: class[Plugin]|None
        """
        return get_identifier_to_object_map("xtheme_plugin").get(identifier)

    @classmethod
    def get_plugin_choices(cls, empty_label=None):
        """
        Get a sorted list of 2-tuples (identifier and name) of available Xtheme plugins.

        Handy for `<select>` boxen.

        :param empty_label: Label for the "empty" choice. If falsy, no empty choice is prepended
        :type empty_label: str|None
        :return: List of 2-tuples
        :rtype: Iterable[tuple[str, str]]
        """
        choices = []
        if empty_label:
            choices.append(("", empty_label))

        for plugin in get_provide_objects("xtheme_plugin"):
            if plugin.identifier:
                choices.append((
                    plugin.identifier,
                    getattr(plugin, "name", None) or plugin.identifier
                ))
        choices.sort()
        return choices


class TemplatedPlugin(Plugin):
    # TODO: Document `TemplatedPlugin` better!
    """
    Convenience base class for plugins that just render a "sub-template" with a given context.
    """

    #: The template to render
    template_name = ""

    #: Variables to copy from the parent context.
    inherited_variables = set()

    #: Variables to copy from the plugin configuration
    config_copied_variables = set()

    engine = None  # template rendering engine

    def get_context_data(self, context):
        """
        Get a context dictionary from a Jinja2 context.

        :param context: Jinja2 rendering context
        :type context: jinja2.runtime.Context
        :return: Dict of vars
        :rtype: dict[str, object]
        """
        vars = {"request": context.get("request")}
        for key in self.required_context_variables:
            vars[key] = context.get(key)
        for key in self.inherited_variables:
            vars[key] = context.get(key)
        for key in self.config_copied_variables:
            vars[key] = self.config.get(key)
        return vars

    def render(self, context):  # doccov: ignore
        vars = self.get_context_data(context)
        if self.engine:
            template = self.engine.get_template(self.template_name)
        else:
            template = get_template(self.template_name)
        return template.render(vars, request=context.get("request"))


def templated_plugin_factory(identifier, template_name, **kwargs):
    """
    A factory (akin to `modelform_factory`) to quickly create simple plugins.

    :param identifier: The unique identifier for the new plugin.
    :type identifier: str
    :param template_name: The template file path this plugin should render
    :type template_name: str
    :param kwargs: Other arguments for the `TemplatedPlugin`/`Plugin` classes.
    :type kwargs: dict
    :return: New `TemplatedPlugin` subclass
    :rtype: class[TemplatedPlugin]
    """
    ns = {
        "identifier": identifier,
        "template_name": template_name,
    }
    ns.update(kwargs)
    ns.setdefault("name", space_case(identifier).title())
    return type(str("%sPlugin" % identifier), (TemplatedPlugin,), ns)
