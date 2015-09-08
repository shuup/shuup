# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from contextlib import contextmanager
from shoop.apps.provides import get_provide_objects, get_identifier_to_object_map
import logging

log = logging.getLogger(__name__)


# TODO: Document how to create Xthemes

class Theme(object):
    """
    Base class for all Xtheme themes.

    This class does not directly correspond to a database object;
    it's used in the rendering, etc. process.

    It does, however, act as a container for a `ThemeSettings` object
    that contains the actual persisted settings etc.
    """

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
    # TODO: Document this
    global_placeholders = []

    # List of (name, FormField) pairs for theme configuration.
    # This might not be used if you override `get_configuration_form`.
    # TODO: Document this
    fields = []

    def __init__(self, settings_obj=None):
        """
        Initialize this theme, with an optional `ThemeSettings` object

        :param settings_obj: A theme settings object for this theme, if one exists.
                             Passing this in will avoid extraneous database queries.
        :type settings_obj: ThemeSettings|None
        """
        self._settings_obj = None
        if settings_obj and settings_obj.theme_identifier == self.identifier:  # fine, let's accept that
            self._settings_obj = settings_obj

    @property
    def settings_obj(self):
        """
        Get a saved settings model for this theme. If one does not yet exist, an unsaved one is returned.

        If one was passed in the ctor, naturally that one is returned.

        :rtype: shoop.xtheme.models.ThemeSettings
        """
        # Ensure this module can be imported from anywhere by lazily importing the model
        from shoop.xtheme.models import ThemeSettings
        if self._settings_obj is None:
            self._settings_obj = ThemeSettings.objects.filter(theme_identifier=self.identifier).first()
            if not self._settings_obj:
                self._settings_obj = ThemeSettings(theme_identifier=self.identifier)
        return self._settings_obj

    def set_current(self):
        """
        Set this theme as the active theme.
        """
        self.settings_obj.activate()

    def get_setting(self, key, default=None):
        """
        Get a setting value for this theme.

        :param key: Setting name
        :type key: str
        :param default: Default value, if the setting is not set
        :type default: object
        :return: Setting value
        :rtype: object
        """
        return self.settings_obj.get_setting(key, default)

    def get_settings(self):
        """
        Get all the currently set settings for the theme as a dict.

        :return: Dict of settings
        :rtype: dict
        """
        return self.settings_obj.get_settings()

    def set_settings(self, *args, **kwargs):
        """
        Set a number of settings for this theme.

        The arguments (*args, **kwargs) are exactly the same as those to `dict`.

        Note: It's better to call this once than `set_setting` several times.
        """
        self.settings_obj.update_settings(dict(*args, **kwargs))

    def set_setting(self, key, value):
        """
        Set a theme setting `key` to the value `value`.

        :param key: Setting name
        :type key: str
        :param value: Setting value
        :type value: object
        """
        self.settings_obj.update_settings({key: value})

    def get_configuration_form(self, form_kwargs):
        """
        Return a ModelForm instance (model=ThemeSettings) for configuring this theme.

        By default, returns a GenericThemeForm (a ModelForm populated from `theme.fields`).

        :param form_kwargs: The keyword arguments that should be used for initializing the form
        :type form_kwargs: dict
        :rtype: django.forms.ModelForm
        """
        from .forms import GenericThemeForm
        return GenericThemeForm(theme=self, **form_kwargs)


_not_set = object()  # Can't use `None` here.
_current_theme_class = _not_set


@contextmanager
def override_current_theme_class(theme_class=_not_set):
    """
    Context manager for overriding the currently active theme class for testing.

    An instance of this class is then returned by `get_current_theme`.

    A falsy value means `None` is returned from `get_current_theme`, which is also
    useful for testing.

    :param theme_class: A theme class object
    :type theme_class: class[Theme]
    """
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
        # Ensure this module can be imported from anywhere by lazily importing the model
        from shoop.xtheme.models import ThemeSettings
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
        if theme_cls is not None:
            theme = theme_cls(settings_obj=ts)
        else:
            log.warn("The active theme %r is not currently installed", ts.theme_identifier)

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
    """
    Activate a theme based on identifier.

    :param identifier: Theme identifier
    :type identifier: str
    """
    theme = get_theme_by_identifier(identifier)
    if not theme:
        raise ValueError("Invalid theme identifier")
    theme.set_current()
