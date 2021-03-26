# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.apps.provides import override_provides
from shuup.core import cache
from shuup.core.models import Shop
from shuup.testing.factories import get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup.themes.classic_gray.theme import ClassicGrayTheme
from shuup.xtheme import (
    get_current_theme,
    get_middleware_current_theme,
    get_theme_by_identifier,
    set_current_theme,
    set_middleware_current_theme,
)
from shuup.xtheme.middleware import XthemeMiddleware
from shuup.xtheme.models import ThemeSettings
from shuup_tests.xtheme.utils import FauxTheme, FauxTheme2


def setup_function(fn):
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("host", ["shop-1.somedomain.com", "shop-test-2.otherdomain.com.br"])
def test_multishops_middleware(rf, host):
    with override_provides("xtheme", ["shuup_tests.xtheme.utils:FauxTheme", "shuup_tests.xtheme.utils:FauxTheme2"]):
        shop1 = Shop.objects.create(identifier="shop1", domain="shop-1")
        shop2 = Shop.objects.create(identifier="shop2", domain="shop-test-2")

        theme_settings_shop1 = ThemeSettings.objects.create(theme_identifier=FauxTheme.identifier, shop=shop1)
        theme_settings_shop2 = ThemeSettings.objects.create(theme_identifier=FauxTheme2.identifier, shop=shop2)

        request = rf.get("/")
        request.META["HTTP_HOST"] = host

        # should apply the correct shop and the template
        apply_request_middleware(request)

        if host == "shop-1.somedomain.com":
            assert request.shop.id == shop1.id
            assert get_middleware_current_theme().identifier == FauxTheme.identifier
            assert get_middleware_current_theme().settings_obj.id == theme_settings_shop1.id
        else:
            assert request.shop.id == shop2.id
            assert get_middleware_current_theme().identifier == FauxTheme2.identifier
            assert get_middleware_current_theme().settings_obj.id == theme_settings_shop2.id


@pytest.mark.django_db
def test_singleshop_middleware(rf):
    default_shop = get_default_shop()
    shop1 = Shop.objects.create(identifier="shop1", domain="shop-1")
    shop2 = Shop.objects.create(identifier="shop2", domain="shop-test-2")

    ThemeSettings.objects.create(theme_identifier=FauxTheme.identifier, shop=shop1)
    ThemeSettings.objects.create(theme_identifier=FauxTheme2.identifier, shop=shop2)

    request = rf.get("/")
    request.META["HTTP_HOST"] = "unknown.anonymous.net"

    # should apply the first shop (the default shop)
    apply_request_middleware(request)

    assert request.shop.id == default_shop.id
    # using the overrided theme (in conftest.py)
    assert get_middleware_current_theme().identifier == ClassicGrayTheme.identifier


@pytest.mark.django_db
def test_set_get_middleware_theme(rf):
    request = rf.get("/")

    default_shop = get_default_shop()
    shop1 = Shop.objects.create(identifier="shop1", domain="shop-1")
    shop2 = Shop.objects.create(identifier="shop2", domain="shop-test-2")

    # theme settings should be for the default shop and ClassicGray (conftest.py)
    request.shop = default_shop
    XthemeMiddleware().process_request(request)
    assert get_middleware_current_theme().identifier == ClassicGrayTheme.identifier
    assert get_middleware_current_theme().settings_obj.shop.id == default_shop.id

    # theme settings should be none, as there is no Active theme for this shop
    request.shop = shop1
    XthemeMiddleware().process_request(request)
    assert get_middleware_current_theme() is None

    # theme settings should be none, as there is no Active theme for this shop
    request.shop = shop2
    XthemeMiddleware().process_request(request)
    assert get_middleware_current_theme() is None

    # manually set the theme
    theme_settings_shop2 = ThemeSettings.objects.create(theme_identifier=FauxTheme2.identifier, shop=shop2)
    set_middleware_current_theme(FauxTheme2(theme_settings_shop2))
    assert get_middleware_current_theme().identifier == FauxTheme2.identifier
    assert get_middleware_current_theme().settings_obj.shop.id == shop2.id


@pytest.mark.django_db
def test_set_get_theme(rf):
    with override_provides("xtheme", ["shuup_tests.xtheme.utils:FauxTheme", "shuup_tests.xtheme.utils:FauxTheme2"]):
        shop1 = Shop.objects.create(identifier="shop1", domain="shop-1")
        shop2 = Shop.objects.create(identifier="shop2", domain="shop-test-2")

        assert get_current_theme(shop1) is None
        assert get_current_theme(shop2) is None

        set_current_theme(FauxTheme2.identifier, shop1)
        assert get_current_theme(shop1).identifier == FauxTheme2.identifier
        assert get_current_theme(shop1).settings_obj is not None

        set_current_theme(FauxTheme.identifier, shop2)
        assert get_current_theme(shop2).identifier == FauxTheme.identifier


@pytest.mark.django_db
def test_get_by_identifier_theme(rf):
    with override_provides("xtheme", ["shuup_tests.xtheme.utils:FauxTheme", "shuup_tests.xtheme.utils:FauxTheme2"]):
        shop1 = Shop.objects.create(identifier="shop1", domain="shop-1")
        shop2 = Shop.objects.create(identifier="shop2", domain="shop-test-2")

        theme = get_theme_by_identifier(FauxTheme2.identifier, shop1)
        assert theme.settings_obj.theme_identifier == FauxTheme2.identifier
        assert theme.settings_obj.shop.id == shop1.id

        theme = get_theme_by_identifier(FauxTheme.identifier, shop2)
        assert theme.settings_obj.theme_identifier == FauxTheme.identifier
        assert theme.settings_obj.shop.id == shop2.id
