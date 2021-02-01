# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import logging
import threading
import warnings
from contextlib import contextmanager

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from shuup.apps.provides import (
    get_identifier_to_object_map, get_provide_objects
)
from shuup.core import cache
from shuup.utils.deprecation import RemovedInFutureShuupWarning
from shuup.utils.importing import load
from shuup.xtheme.extenders import MenuExtenderLocation

log = logging.getLogger(__name__)


# keeps the current middleware state here
_xtheme_middleware_state = threading.local()


def get_theme_cache_key(shop=None):
    return "shop-{}-current_theme".format(shop.id if shop else "default")


# TODO: Document how to create Xthemes
class Theme(object):
    """
    Base class for all the Xtheme themes.

    This class does not directly correspond to a database object;
    it's used in the rendering, etc. process.

    It does, however, act as a container for a `ThemeSettings` object
    that contains the actual persisted settings, etc.
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
    List of dicts containing stylesheet definitions.

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
    Will be Deprecated in the future: List of tuples(path, name) for
    stylesheets provided by this theme.
    """
    stylesheets = []

    # identifier for the stylesheet provided by default
    default_style_identifier = None

    # List of plugin specs used in this template
    plugins = []

    # Guide template location
    guide_template = None

    # Extra configuration themes - it will be included after the configuration form
    extra_config_template = None
    extra_config_extra_css = None
    extra_config_extra_js = None

    def __init__(self, theme_settings=None, shop=None):
        """
        Initialize this theme, with an optional `ThemeSettings` or `Shop` object. Only one should be passed.

        :param theme_settings: A theme settings object for this theme.
        :type theme_settings: ThemeSettings|None

        :param shop: The shop for this theme.
        :type shop: Shop|None
        """
        self._shop = None
        self._theme_settings = None

        if theme_settings:
            if theme_settings.theme_identifier != self.identifier:
                raise ValueError(_("Theme identifiers must match."))

            self._theme_settings = theme_settings
            self._shop = theme_settings.shop

        elif shop:
            from shuup.xtheme.models import ThemeSettings
            self._shop = shop
            self._theme_settings = ThemeSettings.objects.get_or_create(theme_identifier=self.identifier, shop=shop)[0]

        else:
            raise ValueError(_("Either theme_settings or shop should be informed."))

    @property
    def settings_obj(self):
        """
        Get a saved settings model for this theme.

        :rtype: shuup.xtheme.models.ThemeSettings
        """
        return self._theme_settings

    def set_current(self):
        """
        Set this theme as the active theme.
        """
        if not self.settings_obj.active:
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

        .. note:: It's better to call this once instead of calling `set_setting`
                  several times.
        """
        self.settings_obj.update_settings(dict(*args, **kwargs))
    set_settings.alters_data = True

    def set_setting(self, key, value):
        """
        Set a theme setting `key` to the value `value`.

        :param key: Setting name.
        :type key: str
        :param value: Setting value.
        :type value: object
        """
        self.settings_obj.update_settings({key: value})
    set_setting.alters_data = True

    def get_configuration_form(self, form_kwargs):
        """
        Return a ModelForm instance (model=ThemeSettings) for configuring this theme.

        By default, returns a GenericThemeForm (a ModelForm populated from `theme.fields`).

        :param form_kwargs: The keyword arguments that should be used for initializing the form.
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

        :param view_name: View name.
        :type view_name: str
        :return: The extra view, if one exists for the given name.
        :rtype: dict[str, View|callable]|None
        """
        return None

    def get_all_plugin_choices(self, empty_label=None):
        """
        Get grouped list of 2-tuples (identifier and name) of all available Xtheme plugins.

        Super handy for `<select>` boxes.

        :param empty_label: Label for the "empty" choice. If falsy, no empty choice is prepended.
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

        :param empty_label: Label for the "empty" choice. If falsy, no empty choice is prepended.
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
        choices.sort(key=lambda v: v[1])
        return choices

    def get_global_plugin_choices(self, empty_label=None):
        """
        Get a sorted list of 2-tuples (identifier and name) of available global Xtheme plugins.

        Handy for `<select>` boxes.

        :param empty_label: Label for the "empty" choice. If falsy, no empty choice is prepended.
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
        choices.sort(key=lambda v: v[1])
        return choices

    def has_stylesheets(self):
        return bool(self.stylesheets)

    def has_images(self):
        """
        Check if theme has images available.

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
                "Warning! Using list of tuples in `theme.stylesheets` will deprecate "
                "in Shuup 0.5.7. Use list of dictionaries instead.", RemovedInFutureShuupWarning)
        return False

    def get_default_style(self):
        blank = {"stylesheet": "", "name": self.name}
        if not self.has_stylesheets():
            return blank

        old_style = False if isinstance(self.stylesheets[0], dict) else True
        if old_style:
            warnings.warn(
                "Warning! Using list of tuples in `theme.stylesheets` will deprecate "
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

    def render_menu_extensions(self, request, location=MenuExtenderLocation.MAIN_MENU):
        """
        Render menu extensions.

        Some addons want to provide items to main menu.

        :param request:
        :return safe HTML string:
        """
        items = []
        for menu_extender in get_provide_objects("front_menu_extender"):
            extender = menu_extender()
            if extender.location == location:
                items.append(extender.get_rendered_menu_items(request, self))
        return mark_safe("".join(items))


_not_set = object()  # Can't use `None` here.


@contextmanager
def override_current_theme_class(theme_class=_not_set, shop=None):
    """
    Context manager for overriding the currently active theme class for testing.

    An instance of this class is then returned by `get_current_theme`.

    A falsy value means `None` is returned from `get_current_theme`. This is also
    useful for testing.

    :param theme_class: A theme class object.
    :type theme_class: class[Theme]
    """
    # Circular import avoidance:
    from shuup.xtheme.views.extra import clear_view_cache
    old_theme_class = cache.get(get_theme_cache_key(shop))

    if theme_class is _not_set or not theme_class:
        cache.set(get_theme_cache_key(shop), None)
    else:
        from shuup.xtheme.models import ThemeSettings
        theme_settings = ThemeSettings.objects.get_or_create(
            shop=shop,
            theme_identifier=theme_class.identifier
        )[0]
        theme = theme_class(theme_settings)
        set_middleware_current_theme(theme)
        cache.set(get_theme_cache_key(shop), theme)

    clear_view_cache()
    yield

    cache.set(get_theme_cache_key(shop), old_theme_class)
    clear_view_cache()


def get_current_theme(shop):
    """
    Get the currently active theme object.

    :param shop: The shop to get the active theme.
    :type shop: shuup.core.models.Shop
    :return: Theme object or None
    :rtype: Theme
    """
    value = cache.get(get_theme_cache_key(shop))
    if value:
        set_middleware_current_theme(value)
        return value

    theme = _get_current_theme(shop)
    cache.set(get_theme_cache_key(shop), theme)
    # set this theme as the current for this thread
    set_middleware_current_theme(theme)

    return theme


def set_middleware_current_theme(theme):
    """"
    Set the theme as the current for this thread.
    """
    _xtheme_middleware_state.theme = theme


def get_middleware_current_theme():
    """
    Return the current middleware state theme.
    """
    return getattr(_xtheme_middleware_state, "theme", None)


def get_theme_by_identifier(identifier, shop):
    """
    Get an instantiated theme by identifier.

    :param identifier: Theme identifier.
    :type identifier: str

    :param shop: Shop to fetch the theme settings.
    :type shop: shuup.core.models.Shop

    :return: Theme object or None
    :rtype: Theme
    """
    for theme_cls in get_provide_objects("xtheme"):
        if theme_cls.identifier == identifier:
            from shuup.xtheme.models import ThemeSettings
            theme_settings = ThemeSettings.objects.get_or_create(
                theme_identifier=identifier,
                shop=shop
            )[0]

            return theme_cls(theme_settings=theme_settings)

    return None  # No such thing.


def set_current_theme(identifier, shop):
    """
    Activate a theme based on identifier.

    :param identifier: Theme identifier.
    :type identifier: str
    :param shop: Shop to fetch the theme settings.
    :type shop: shuup.core.models.Shop
    :return: Activated theme
    :rtype: Theme
    """
    cache.bump_version(get_theme_cache_key(shop))
    theme = get_theme_by_identifier(identifier, shop)
    if not theme:
        raise ValueError("Error! Invalid theme identifier.")
    theme.set_current()
    cache.set(get_theme_cache_key(shop), theme)
    set_middleware_current_theme(theme)
    return theme


def _get_current_theme(shop):
    theme = None
    try:
        # Ensure this module can be imported from anywhere by lazily importing the model
        from shuup.xtheme.models import ThemeSettings
        theme_settings = ThemeSettings.objects.filter(active=True, shop=shop).first()

        # no active found, take the first and activate
        if not theme_settings:
            theme_settings = ThemeSettings.objects.filter(shop=shop).first()

            if theme_settings:
                theme_settings.activate()
                theme_settings.refresh_from_db()

    except Exception as exc:
        # This is unfortunate and weird, but I don't want other tests to depend
        # on Xtheme's state or require the `djangodb` mark for every test.
        # So we silence exceptions with pytest-django's "Database access not allowed"
        # message here and let everything else pass.
        if "Database access not allowed" not in str(exc):
            raise
        theme_settings = None

    if theme_settings:
        theme_cls = get_identifier_to_object_map("xtheme").get(theme_settings.theme_identifier)
        if theme_cls is not None:
            theme = theme_cls(theme_settings=theme_settings)
        else:
            log.warn("Warning! The active theme %r is currently not installed.", theme_settings.theme_identifier)

    return theme
