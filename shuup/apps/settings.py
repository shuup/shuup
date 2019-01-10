# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import django.apps
import django.conf
from django.core.exceptions import ImproperlyConfigured

#: Stores all known settings by their name (collected from the apps)
_KNOWN_SETTINGS = {}


def collect_settings_from_app(app_config):
    try:
        settings_module = app_config.get_default_settings_module()
    except ImportError:
        return
    collect_settings(app_name=app_config.name, settings_module=settings_module)


def collect_settings(app_name, settings_module):
    for (name, value) in vars(settings_module).items():
        if _is_valid_setting_name(name):
            _declare_setting(app_name, settings_module, name, value)
            if not hasattr(django.conf.settings, name):
                setattr(django.conf.settings, name, value)


def _declare_setting(app_name, module, name, default):
    if name in _KNOWN_SETTINGS:
        other_app = _KNOWN_SETTINGS[name].app_name
        raise ImproperlyConfigured(
            'Apps %s and %s define same setting %s' % (
                other_app, app_name, name))
    _KNOWN_SETTINGS[name] = Setting(
        name=name,
        default=default,
        app_name=app_name,
        module=module.__name__,
    )


def get_known_settings():
    """
    Get all settings known to Shuup.

    :rtype: Iterable[Setting]
    """
    return _KNOWN_SETTINGS.values()


class Setting(object):
    def __init__(self, name, default, app_name, module):
        self.name = name
        self.default = default
        self.app_name = app_name
        self.module = module

    def __repr__(self):
        items = ('%s=%r' % (k, v) for (k, v) in self.__dict__.items())
        return '%s(%s)' % (type(self).__name__, ', '.join(items))


def _is_valid_setting_name(name):
    return name.isupper() and not name.startswith('_')


def validate_templates_configuration():
    """
    Validate the TEMPLATES configuration in the Django settings.

    Shuup's admin and default frontend require some Django-Jinja configuration, so
    let's make sure clients configure their projects correctly.

    :raises: Raises ImproperlyConfigured if the configuration does not seem valid.
    :return:
    :rtype:
    """
    for template_engine in django.conf.settings.TEMPLATES:
        backend = template_engine["BACKEND"]
        if "DjangoTemplates" in backend:
            raise ImproperlyConfigured(
                "The DjangoTemplates engine was encountered in your template configuration "
                "before Django-Jinja. This configuration will not work correctly with Shuup."
            )
        if backend == "django_jinja.backend.Jinja2":
            if not template_engine.get("APP_DIRS"):
                raise ImproperlyConfigured(
                    "You have the django_jinja backend configured, but it is not configured to "
                    "take application template directories into account. Set APP_DIRS = True."
                )
            options = template_engine.get("OPTIONS") or {}
            if options.get("match_extension") != ".jinja":
                raise ImproperlyConfigured(
                    "You have the django_jinja backend configured, but it is not configured to "
                    "render `.jinja` templates. Set OPTIONS.match_extension to \".jinja\"."
                )
            return True
    raise ImproperlyConfigured(
        "The `django_jinja` template backend was not encountered in your TEMPLATES configuration. "
        "See the Shuup or Django-Jinja documentation on more information how to configure things correctly."
    )


def reload_apps():
    import django
    from django.contrib.staticfiles.finders import get_finder
    # Clear cache for any AppDirectoriesFinder instance.
    # This should be done before Django apps is reloaded.
    get_finder.cache_clear()

    _KNOWN_SETTINGS.clear()
    django.apps.apps.app_configs.clear()
    django.apps.apps.ready = False
    django.setup()
