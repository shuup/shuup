# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import logging
import warnings
from contextlib import contextmanager

from django.utils.translation import ugettext_lazy as _

from shuup.apps.provides import (
    get_identifier_to_object_map, get_provide_objects
)
from shuup.core import cache
from shuup.utils.deprecation import RemovedInFutureShuupWarning
from shuup.utils.importing import load

log = logging.getLogger(__name__)

THEME_CACHE_KEY = "current_theme"


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

    # Directory prefix for this theme's default template files.
    # If `None`, the default `shuup.front` templates is used instead.
    default_template_dir = None

    # List of global placeholder names.
    # TODO: (These could be ignored in per-view editing, or something?)
    # TODO: Document this
    global_placeholders = []

    # List of (name, FormField) pairs for theme configuration.
    # This might not be used if you override `get_configuration_form`.
    # TODO: Document this
    fields = []

    """
    List of dicts containing stylesheet definitions

    Each dict must contain following values:
        * `identifier` internal identifier of the stylesheet
          definition. Identifier is used on theme selection.
          If your stylesheet doesn't define the `identifier`
          the images cannot be shown in theme selector.
        * `stylesheet` with a value of the css file path
        * `name` with a name of the stylesheet

    Following values are not mandatory:
        * `images` a list of image paths. Images are shown
          when merchant makes decisions on what theme to use.

    Example:
        stylesheets = [
            {
                "identifier": "my_style",
                "stylesheet": "path/to/style.css",
                "name": _("My Style"),
                "images: ["path/to/image.png", "path/to/image2.png"]
            }
        ]
    Will be Deprecated in future: List of tuples(path, name) for
    stylesheets provided by this theme.
    """
    stylesheets = []

    # identifier for the stylesheet provided by default
    default_style_identifier = None

    # List of plugin specs used in this template
    plugins = []

    # Guide template location
    guide_template = None

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

        :rtype: shuup.xtheme.models.ThemeSettings
        """
        # Ensure this module can be imported from anywhere by lazily importing the model
        from shuup.xtheme.models import ThemeSettings
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
    set_current.alters_data = True

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

        The arguments are exactly the same as those to `dict`.

        .. note:: It's better to call this once than `set_setting`
                  several times.
        """
        self.settings_obj.update_settings(dict(*args, **kwargs))
    set_settings.alters_data = True

    def set_setting(self, key, value):
        """
        Set a theme setting `key` to the value `value`.

        :param key: Setting name
        :type key: str
        :param value: Setting value
        :type value: object
        """
        self.settings_obj.update_settings({key: value})
    set_setting.alters_data = True

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

    def get_view(self, view_name):
        """
        Get an extra view for this theme.

        Views may be either normal Django functions or CBVs (or anything that has `.as_view()` really).
        Falsy values are considered "not found".

        :param view_name: View name
        :type view_name: str
        :return: The extra view, if one exists for the given name.
        :rtype: dict[str, View|callable]|None
        """
        return None

    def get_all_plugin_choices(self, empty_label=None):
        """
        Get grouped list of 2-tuples (identifier and name) of all available Xtheme plugins.

        Super handy for `<select>` boxes.

        :param empty_label: Label for the "empty" choice. If falsy, no empty choice is prepended
        :type empty_label: str|None
        :return: List of 2-tuples
        :rtype: Iterable[tuple[str, str]]
        """
        choices = []
        if empty_label:
            choices.append(("", empty_label))
        choices += [(_("Global plugins"), self.get_global_plugin_choices())]
        choices += [(_("Theme plugins"), self.get_theme_plugin_choices())]
        return choices

    def get_theme_plugin_choices(self, empty_label=None):
        """
        Get a sorted list of 2-tuples (identifier and name) of available theme specific Xtheme plugins.

        Handy for `<select>` boxes.

        :param empty_label: Label for the "empty" choice. If falsy, no empty choice is prepended
        :type empty_label: str|None
        :return: List of 2-tuples
        :rtype: Iterable[tuple[str, str]]
        """
        choices = []
        if empty_label:
            choices.append(("", empty_label))

        for plugin_spec in self.plugins:
            plugin = load(plugin_spec)
            choices.append((
                plugin.identifier,
                getattr(plugin, "name", None) or plugin.identifier
            ))
        choices.sort()
        return choices

    def get_global_plugin_choices(self, empty_label=None):
        """
        Get a sorted list of 2-tuples (identifier and name) of available global Xtheme plugins.

        Handy for `<select>` boxes.

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

    def has_stylesheets(self):
        return bool(self.stylesheets)

    def has_images(self):
        """
        Check if theme has images available

        :return: True or False
        :rtype: bool
        """
        if not self.has_stylesheets():
            return False

        if isinstance(self.stylesheets[0], dict):
            for sheet in self.stylesheets:
                if sheet.get("images", None):
                    return True
        else:
            warnings.warn(
                "Using list of tuples in theme.stylesheets will deprecate "
                "in Shuup 0.5.7. Use list of dictionaries instead.", RemovedInFutureShuupWarning)
        return False

    def get_default_style(self):
        blank = {"stylesheet": "", "name": self.name}
        if not self.has_stylesheets():
            return blank

        old_style = False if isinstance(self.stylesheets[0], dict) else True
        if old_style:
            warnings.warn(
                "Using list of tuples in theme.stylesheets will deprecate "
                "in Shuup 0.5.7. Use list of dictionaries instead.", RemovedInFutureShuupWarning)

            # just return this, no identifier available
            stylesheet, name = self.stylesheets[0]
            return {
                "stylesheet": stylesheet,
                "name": name
            }

        if not self.default_style_identifier:
            return self.stylesheets[0]
        else:
            for stylesheet in self.stylesheets:
                if stylesheet.identifier == self.default_style_identifier:
                    return stylesheet
        return blank


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
    # Circular import avoidance:
    from shuup.xtheme.views.extra import clear_view_cache
    old_theme_class = _current_theme_class
    _current_theme_class = theme_class
    clear_view_cache()
    yield
    _current_theme_class = old_theme_class
    clear_view_cache()


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

    value = cache.get(THEME_CACHE_KEY)
    if value:
        return value

    if request and hasattr(request, "_current_xtheme"):
        return request._current_xtheme

    theme = _get_current_theme()

    if request:
        request._current_xtheme = theme

    cache.set(THEME_CACHE_KEY, theme)
    return theme


def get_theme_by_identifier(identifier, settings_obj=None):
    """
    Get an instantiated theme by identifier.

    :param identifier: Theme identifier
    :type identifier: str
    :param settings_obj: Optional ThemeSettings object for the theme constructor
    :type settings_obj: shuup.xtheme.models.ThemeSettings
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
    :return: Activated theme
    :rtype: Theme
    """
    cache.bump_version(THEME_CACHE_KEY)
    theme = get_theme_by_identifier(identifier)
    if not theme:
        raise ValueError("Invalid theme identifier")
    theme.set_current()
    cache.set(THEME_CACHE_KEY, theme)
    return theme


def _get_current_theme():
    theme = None
    try:
        # Ensure this module can be imported from anywhere by lazily importing the model
        from shuup.xtheme.models import ThemeSettings
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
    return theme
