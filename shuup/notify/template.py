# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from jinja2.sandbox import SandboxedEnvironment

from shuup.utils.django_compat import force_text
from shuup.utils.importing import cached_load


class NoLanguageMatches(Exception):
    pass


def get_sandboxed_template_environment(context, **kwargs):
    """
    Returns a Jinja2 enviroment for rendering templates in notifications

    :param context: Script context.
    :type context: shuup.notify.script.Context
    :param kwargs: extra args.
    :type kwargs: dict
    :return: The environment used to render.
    :rtype: jinja2.environment.Environment
    """
    env_kwargs = dict()
    if "html_intent" in kwargs:
        env_kwargs = dict(autoescape=kwargs["html_intent"])
    return SandboxedEnvironment(**env_kwargs)


def render_in_context(context, template_text, html_intent=False):
    """
    Render the given Jinja2 template text in the script context.

    :param context: Script context.
    :type context: shuup.notify.script.Context
    :param template_text: Jinja2 template text.
    :type template_text: str
    :param html_intent: Is the template text intended for HTML output?
                        This currently turns on autoescaping.
    :type html_intent: bool
    :return: Rendered template text.
    :rtype: str
    :raises: Whatever Jinja2 might happen to raise.
    """

    environment_provider = cached_load("SHUUP_NOTIFY_TEMPLATE_ENVIRONMENT_PROVIDER")
    env = environment_provider(context=context, html_intent=html_intent)
    template = env.from_string(template_text)
    return template.render(context.get_variables())


class Template(object):
    def __init__(self, context, data):
        """
        :param context: Script context.
        :type context: shuup.notify.script.Context
        :param data: Template data dictionary.
        :type data: dict
        """
        self.context = context
        self.data = data

    def _get_language_data(self, language, fields):
        data = self.data.get(force_text(language).lower(), {})
        for key, field in fields.items():
            if hasattr(field, "initial"):
                data.setdefault(key, field.initial)
        return data

    def has_language(self, language, fields):
        data = self._get_language_data(language, fields)
        return set(data.keys()) >= set(fields.keys())

    def render(self, language, fields):
        """
        Render this template in the given language,
        returning the given fields.

        :param language: Language code (ISO 639-1 or ISO 639-2).
        :type language: str
        :param fields: Desired fields to render.
        :type fields: list[str]
        :return: Dict of field -> rendered content.
        :rtype: dict[str, str]
        """
        data = self._get_language_data(language, fields)

        rendered = {}

        for field in fields.keys():
            field_template = data.get(field)
            if field_template:  # pragma: no branch
                rendered[field] = render_in_context(self.context, field_template, html_intent=False)

        return rendered

    def render_first_match(self, language_preferences, fields):
        # TODO: Document
        for language in language_preferences:
            if self.has_language(language, fields):
                rendered = self.render(language=language, fields=fields)
                rendered["_language"] = language
                return rendered
        raise NoLanguageMatches("Error! No language in template matches any of languages `%r` for fields `%r`." % (
            language_preferences, fields.keys()
        ))
