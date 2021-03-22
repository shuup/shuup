# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.translation import activate

from shuup.testing import factories
from shuup.themes.classic_gray.theme import ClassicGrayTheme
from shuup.utils.django_compat import reverse
from shuup.xtheme.models import ThemeSettings
from shuup.xtheme.testing import override_current_theme_class
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_product_view_prices_and_basket_visibility(rf):
    activate("en")
    product_sku = "test-123"
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    default_price = 11
    product = factories.create_product(product_sku, shop=shop, supplier=supplier, default_price=default_price)

    assert ThemeSettings.objects.count() == 1
    theme_settings = ThemeSettings.objects.first()
    assert theme_settings.shop == shop
    assert theme_settings.theme_identifier == ClassicGrayTheme.identifier

    assert not theme_settings.get_setting("hide_prices")
    assert not theme_settings.get_setting("catalog_mode")

    with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
        c = SmartClient()
        soup = c.soup(reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug}))
        assert _is_basket_in_soup(soup)
        assert _is_price_in_soup(soup, default_price)
        assert _is_add_to_basket_button_in_soup(soup)

    theme_settings.update_settings({"catalog_mode": True})
    with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
        c = SmartClient()
        soup = c.soup(reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug}))
        assert not _is_basket_in_soup(soup)
        assert not _is_add_to_basket_button_in_soup(soup)
        assert _is_price_in_soup(soup, default_price)

    theme_settings.update_settings({"hide_prices": True, "catalog_mode": False})
    with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
        c = SmartClient()
        soup = c.soup(reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug}))
        assert not _is_add_to_basket_button_in_soup(soup)
        assert not _is_basket_in_soup(soup)
        assert not _is_price_in_soup(soup, default_price)


def _is_price_in_soup(soup, expected_price_value):
    product_price_div = soup.find("div", {"class": "product-price-div"})
    if not product_price_div:
        return False

    product_price_span = product_price_div.find("span", {"class": "product-price"})
    if not product_price_span:
        return False

    return "%s" % expected_price_value in product_price_span.find("strong").text


def _is_basket_in_soup(soup):
    cart_dropdown = soup.find("li", {"class": "dropdown cart"})
    if not cart_dropdown:
        return False

    return cart_dropdown.find("i", {"class": "fa-shopping-cart"}) is not None


def _is_add_to_basket_button_in_soup(soup):
    add_to_cart_div = soup.find("div", {"class": "btn-add-to-cart"})
    if not add_to_cart_div:
        return False

    return add_to_cart_div.find("i", {"class": "fa-shopping-cart"}) is not None
