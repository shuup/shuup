# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
"""
Shoop Registration Add-on
=========================

The shoop.front.apps.registration add-on provides simple user
registration and email token based activation.

It is based on the django-registration-redux package.

Installation
------------

Add ``registration`` and ``shoop.front.apps.registration``
into your ``INSTALLED_APPS`` (and run migrations, of course).

The application registers its URLs via the ``front_urls`` provides
mechanism.

URL names
---------

* ``shoop:registration_register`` -- the entry point for registration.
"""

import django.conf
from registration.signals import user_activated, login_user
from shoop.apps import AppConfig


class RegistrationAppConfig(AppConfig):
    name = "shoop.front.apps.registration"
    verbose_name = "Shoop Frontend - User Registration"
    label = "shoop_front.registration"

    required_installed_apps = {
        "registration": "django-registration-redux is required for user registration and activation"
    }

    provides = {
        "front_urls": [
            "shoop.front.apps.registration.urls:urlpatterns"
        ],
    }

    def ready(self):
        if not hasattr(django.conf.settings, "ACCOUNT_ACTIVATION_DAYS"):
            # Patch settings to include ACCOUNT_ACTIVATION_DAYS;
            # it's a setting owned by `django-registration-redux`,
            # but not set to a default value. If it's not set, a crash
            # will occur when attempting to create an account, so
            # for convenience, we're doing what `django-registration-redux`
            # didn't wanna.
            django.conf.settings.ACCOUNT_ACTIVATION_DAYS = 7

        if not hasattr(django.conf.settings, "REGISTRATION_AUTO_LOGIN"):
            # By default, Django-Registration considers this False, but
            # we override it to True. unless otherwise set by the user.
            django.conf.settings.REGISTRATION_AUTO_LOGIN = True

            # connect signal here since the setting value has changed
            user_activated.connect(login_user)

        if not hasattr(django.conf.settings, "REGISTRATION_EMAIL_HTML"):
            # We only provide txt templates out of the box, so default to
            # false for HTML mails.
            django.conf.settings.REGISTRATION_EMAIL_HTML = False

default_app_config = "shoop.front.apps.registration.RegistrationAppConfig"
