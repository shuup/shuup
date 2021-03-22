# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings
from django.test.client import Client

from shuup.apps.provides import override_provides
from shuup.core import cache
from shuup.testing.factories import get_default_shop
from shuup.themes.classic_gray.theme import ClassicGrayTheme
from shuup.utils.django_compat import reverse
from shuup.xtheme._theme import _get_current_theme, set_current_theme
from shuup.xtheme.models import ThemeSettings


@pytest.mark.django_db
def test_classic_gray_theme_settings(admin_user):
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_cache",
            }
        }
    ):
        cache.init_cache()
        shop = get_default_shop()

        with override_provides("xtheme", ["shuup.themes.classic_gray.theme:ClassicGrayTheme"]):
            set_current_theme(ClassicGrayTheme.identifier, shop)
            theme = _get_current_theme(shop)
            assert isinstance(theme, ClassicGrayTheme)
            ThemeSettings.objects.all().delete()

            client = Client()
            admin_user.set_password("admin")
            admin_user.save()
            client.login(username=admin_user.username, password="admin")

            theme_config_url = reverse(
                "shuup_admin:xtheme.config_detail", kwargs=dict(theme_identifier=ClassicGrayTheme.identifier)
            )
            response = client.get(theme_config_url)
            assert response.status_code == 200

            assert theme.get_setting("shop_logo_width") is None
            assert theme.get_setting("shop_logo_height") is None
            assert theme.get_setting("shop_logo_alignment") is None
            assert theme.get_setting("shop_logo_aspect_ratio") is None

            settings = {"stylesheet": "shuup/classic_gray/blue/style.css"}
            response = client.post(theme_config_url, data=settings)
            assert response.status_code == 302

            theme = _get_current_theme(shop)
            for key, value in settings.items():
                assert theme.get_setting(key) == value
