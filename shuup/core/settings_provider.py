# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings

from shuup.apps.provides import get_provide_objects
from shuup.apps.settings import get_configuration_setting


class BaseSettingsProvider(object):
    """
    This class is deceprecated as the shuup settings were moved to configuration.
    """

    provided_settings = []

    def offers(self, setting_key):
        return bool(setting_key in self.provided_settings)

    def get_setting_value(self, setting_key):
        return None


class ShuupSettings(object):
    """
    This class is deceprecated as the shuup settings were moved to configuration. Use shuup.configuration.get instead.
    """

    @classmethod
    def get_setting(cls, setting_key):
        configuration_value = get_configuration_setting(setting_key)
        if configuration_value is not None:
            return configuration_value

        for provider_cls in get_provide_objects("shuup_settings_provider"):
            provider = provider_cls()
            if provider.offers(setting_key):
                return provider.get_setting_value(setting_key)
        return getattr(settings, setting_key)
