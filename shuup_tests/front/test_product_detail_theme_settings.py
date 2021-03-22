# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup

from shuup.testing import factories
from shuup.themes.classic_gray.theme import ClassicGrayTheme
from shuup.utils.django_compat import reverse
from shuup.xtheme.models import ThemeSettings
from shuup.xtheme.testing import override_current_theme_class


def _get_product_detail_soup(client, product):
    url = reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug})
    response = client.get(url)
    return BeautifulSoup(response.content)


@pytest.mark.django_db
def test_product_detail_theme_configs(client):
    shop = factories.get_default_shop()
    product = factories.create_product("sku", shop=shop, default_price=30)

    # Show only product description section
    assert ThemeSettings.objects.count() == 1
    theme_settings = ThemeSettings.objects.first()
    theme_settings.update_settings({"product_detail_tabs": ["description"]})

    with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
        soup = _get_product_detail_soup(client, product)
        assert soup.find("div", attrs={"class": "product-tabs"})
        tabs = soup.find_all("ul", attrs={"class": "nav-tabs"})[0].find_all("li")
        assert len(tabs) == 1
        assert "Description" in tabs[0].text

    # disable product details completely
    theme_settings.update_settings({"show_product_detail_section": False})
    with override_current_theme_class(ClassicGrayTheme, shop):
        soup = _get_product_detail_soup(client, product)
        assert not soup.find("div", attrs={"class": "product-tabs"})
