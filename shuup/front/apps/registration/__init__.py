# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
Shuup Registration Add-on
=========================

The shuup.front.apps.registration add-on provides simple user
registration and email token based activation.

It is based on the django-registration-redux package.

Installation
------------

Add ``registration`` and ``shuup.front.apps.registration``
into your ``INSTALLED_APPS`` (and run migrations, of course).

The application registers its URLs via the ``front_urls`` provides
mechanism.

URL names
---------

* ``shuup:registration_register`` -- the entry point for registration.
"""

import django.conf
from registration.signals import login_user, user_activated

from shuup.apps import AppConfig


class RegistrationAppConfig(AppConfig):
    name = "shuup.front.apps.registration"
    verbose_name = "Shuup Frontend - User Registration"
    label = "shuup_front.registration"

    required_installed_apps = {
        "registration": "django-registration-redux is required for user registration and activation"
    }

    provides = {
        "front_urls": [
            "shuup.front.apps.registration.urls:urlpatterns"
        ],
        "notify_event": [
            "shuup.front.apps.registration.notify_events:RegistrationReceived"
        ],
        "notify_script_template": [
            "shuup.front.apps.registration.notify_events:RegistrationReceivedEmailScriptTemplate"
        ]
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


default_app_config = "shuup.front.apps.registration.RegistrationAppConfig"
