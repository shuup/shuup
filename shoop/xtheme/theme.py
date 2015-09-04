# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from contextlib import contextmanager
from shoop.apps.provides import get_provide_objects, get_identifier_to_object_map
from shoop.xtheme.models import ThemeSettings


class Theme(object):
    # The identifier for this theme. Used for theme selection.
    # Must be set in actual themes!
    identifier = None

    # The printable name for this theme.
    name = ""

    # The author for this theme, for posterity.
    author = ""

    # Directory prefix for this theme's template files.
    # If `None`, the `identifier` is used instead
    template_dir = None

    # List of global placeholder names.
    # TODO: (These could be ignored in per-view editing, or something?)
    global_placeholders = []

    # List of (name, FormField) pairs for theme configuration.
    # This might not be used if you override `get_configuration_form`.
    fields = []

    def __init__(self, settings_obj=None):
        self._settings_obj = None
        if settings_obj and settings_obj.theme_identifier == self.identifier:  # fine, let's accept that
            self._settings_obj = settings_obj

    @property
    def settings_obj(self):
        # Try to ensure this module can be imported from anywhere by lazily importing the model
        from shoop.xtheme.models import ThemeSettings
        if self._settings_obj is None:
            self._settings_obj = ThemeSettings.objects.filter(theme_identifier=self.identifier).first()
            if not self._settings_obj:
                self._settings_obj = ThemeSettings(theme_identifier=self.identifier)
        return self._settings_obj

    def set_current(self):
        self.settings_obj.activate()

    def get_setting(self, key, default=None):
        return self.settings_obj.get_setting(key, default)

    def get_settings(self):
        return self.settings_obj.get_settings()

    def set_settings(self, *args, **kwargs):
        self.settings_obj.update_settings(dict(*args, **kwargs))

    def set_setting(self, key, value):
        self.settings_obj.update_settings({key: value})

    def get_configuration_form(self, form_kwargs):
        """
        Return a ModelForm instance (model=ThemeSettings) for configuring this theme.

        By default, returns a GenericThemeForm (a ModelForm populated from `theme.fields`).

        :type form_kwargs: dict
        :rtype: django.forms.ModelForm
        """
        from .forms import GenericThemeForm
        return GenericThemeForm(theme=self, **form_kwargs)


_not_set = object()  # Can't use `None` here.
_current_theme_class = _not_set


@contextmanager
def override_current_theme_class(theme_class):
    global _current_theme_class
    old_theme_class = _current_theme_class
    _current_theme_class = theme_class
    yield
    _current_theme_class = old_theme_class


def get_current_theme(request=None):
    """
    Get the currently active theme object.

    :param request: Request, if available
    :type request: HttpRequest|None
    :return: Theme object or None
    :rtype: Theme
    """
    if _current_theme_class is not _not_set:
        if _current_theme_class:
            return _current_theme_class()
        return None  # No theme (usually for testing)

    if request and hasattr(request, "_current_xtheme"):
        return request._current_xtheme
    theme = None

    try:
        ts = ThemeSettings.objects.filter(active=True).first()
    except Exception as exc:
        # This is unfortunate and weird, but I don't want other tests to depend
        # on Xtheme's state or require the `djangodb` mark for every test.
        # So we silence exceptions with pytest-django's "Database access not allowed"
        # message here and let everything else pass.
        if "Database access not allowed" not in str(exc):
            raise
        ts = None

    if ts:
        theme_cls = get_identifier_to_object_map("xtheme").get(ts.theme_identifier)
        theme = theme_cls(settings_obj=ts)

    if request:
        request._current_xtheme = theme
    return theme


def get_theme_by_identifier(identifier, settings_obj=None):
    """
    Get an instantiated theme by identifier.

    :param identifier: Theme identifier
    :type identifier: str
    :param settings_obj: Optional ThemeSettings object for the theme constructor
    :type settings_obj: shoop.xtheme.models.ThemeSettings
    :return: Theme object or None
    :rtype: Theme
    """
    for theme_cls in get_provide_objects("xtheme"):
        if theme_cls.identifier == identifier:
            return theme_cls(settings_obj=settings_obj)
    return None  # No such thing.


def set_current_theme(identifier):
    theme = get_theme_by_identifier(identifier)
    if not theme:
        raise ValueError("Invalid theme identifier")
    theme.set_current()
