# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Shuup Application API
=====================

Every Shuup Application should define an app config class derived from
`shuup.apps.AppConfig`:class:.

.. _apps-settings:

Settings
--------

To define settings for a Shuup Application, add a ``settings.py`` file
to your app and define each setting as a module level variable with
uppercase name.  The values of these setting variables will be used as
the default values for the settings.  To document a setting, add a
special comment block using '#: ' prefixed lines just before the
setting assignment line.

Default values can then be changed normally by defining the changed
value in your Django settings module.  To read a value of a setting use
the `django.conf.settings` interface.

For example, if a fancy app lives in a Python package named `fancyapp`,
its settings will be in module `fancyapp.settings` and if it contains
something like this

.. code-block:: python

   #: Number of donuts to use
   #:
   #: Must be less than 42.
   FANCYAPP_NUMBER_OF_DONUTS = 3

then this would define a setting `FANCYAPP_NUMBER_OF_DONUTS` with a
default value of 3.

See also source code of :obj:`shuup.core.settings`.

.. _apps-naming-settings:

Naming Settings
^^^^^^^^^^^^^^^

Applications in :term:`Shuup Base` distribution should use the following
rules for naming their settings.

 1. Each setting should be prefixed with the string `SHUUP_`
 2. Boolean toggle settings should have a verb in imperative mood as
    part of the name, e.g. `SHUUP_ALLOW_ANONYMOUS_ORDERS`,
    `SHUUP_ENABLE_ATTRIBUTES` or `SHUUP_ENABLE_MULTIPLE_SHOPS`.
 3. Setting that is used to locate a replaceable module should have
    suffix `_SPEC` or `_SPECS` (if the setting is a list or mapping of
    those), e.g. `SHUUP_PRICING_MODULE_SPEC`.
 4. Setting names do NOT have to be prefixed with the application name.
    For example, `SHUUP_BASKET_VIEW_SPEC` which is not prefixed with
    `SHUUP_FRONT` even though it is from `shuup.front` application.
 5. Setting names should be unique; if two applications define a setting
    with a same name, they cannot be enabled in the same installation.

.. _apps-settings-override-warning:

.. warning::

   When you have a settings file :file:`your_app/settings.py`, do not
   import Django's settings in :file:`your_app/__init__.py` with

   .. code-block:: python

      from django.conf import settings

   since that will make ``your_app.settings`` ambiguous. It may point to
   :obj:`django.conf.settings` when ``your_app.settings`` is not yet
   imported, or when it is imported, it will point to module defined by
   :file:`your_app/settings.py`.
"""
from __future__ import unicode_literals

import importlib

import django.apps
import django.conf
from django.core.exceptions import ImproperlyConfigured

from .settings import collect_settings_from_app, get_known_settings

__all__ = ["AppConfig", "get_known_settings"]


class AppConfig(django.apps.AppConfig):
    #: Name of the settings module for this app
    default_settings_module = ".settings"

    #: Apps that are required to be in INSTALLED_APPS for this app
    #:
    #: This may also be a dict of the form {app_name: reason}
    #: where the reason will then be listed in the `ImproperlyConfigured`
    #: exception.
    required_installed_apps = ()

    #: See :doc:`/provides` for details about the ``provides`` variable.
    provides = {}

    def __init__(self, *args, **kwargs):
        super(AppConfig, self).__init__(*args, **kwargs)
        collect_settings_from_app(self)
        self._check_required_installed_apps()

    def get_default_settings_module(self):
        """
        Get default settings module.

        :return: the settings module.
        :raises: ImportError if no such module exists.
        """
        mod_name = self.default_settings_module
        pkg_name = self.module.__name__
        return importlib.import_module(mod_name, package=pkg_name)

    def _get_app_require_reason(self, app_name):
        try:
            return self.required_installed_apps[app_name]
        except (TypeError, KeyError):
            return "required"

    def _check_required_installed_apps(self):
        required_apps = set(self.required_installed_apps)
        installed_apps = set(django.conf.settings.INSTALLED_APPS)
        missing_apps = required_apps - installed_apps
        if missing_apps:
            information = ", ".join(
                "%s (%s)" % (app_name, self._get_app_require_reason(app_name)) for app_name in sorted(missing_apps)
            )
            raise ImproperlyConfigured(
                "Error! `%s` requires the following INSTALLED_APPS: `%s`" % (self.name, information)
            )
