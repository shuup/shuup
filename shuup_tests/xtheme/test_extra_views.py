# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.utils.encoding import force_text

from shuup.core import cache
from shuup.testing.factories import get_default_shop
from shuup.xtheme.testing import override_current_theme_class
from shuup.xtheme.views.extra import extra_view_dispatch
from shuup_tests.xtheme.utils import H2G2Theme


def test_xtheme_extra_views(rf):
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_cache",
            }
        }
    ):
        cache.init_cache()
        with override_current_theme_class(H2G2Theme, get_default_shop()):
            request = rf.get("/", {"name": "Arthur Dent"})
            request.shop = get_default_shop()
            # Simulate /xtheme/greeting
            response = extra_view_dispatch(request, "greeting")
            assert force_text(response.content) == "So long, and thanks for all the fish, Arthur Dent"
            # Try that again (to exercise the _VIEW_CACHE code path):
            response = extra_view_dispatch(request, "greeting")
            assert force_text(response.content) == "So long, and thanks for all the fish, Arthur Dent"
            # Now test that CBVs work
            assert not extra_view_dispatch(request, "faux").content


def test_xtheme_extra_view_exceptions(rf):
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test_configuration_cache",
            }
        }
    ):
        cache.init_cache()
        with override_current_theme_class(H2G2Theme, get_default_shop()):
            request = rf.get("/")
            request.shop = get_default_shop()
            assert extra_view_dispatch(request, "vogons").status_code == 404
            with pytest.raises(ImproperlyConfigured):
                assert extra_view_dispatch(request, "true")
