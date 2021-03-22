# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from bs4 import BeautifulSoup
from django.test import override_settings

from shuup.core.models import Supplier
from shuup.testing import factories
from shuup.testing.models import SupplierPrice
from shuup.themes.classic_gray.theme import ClassicGrayTheme
from shuup.utils.django_compat import reverse
from shuup.xtheme.models import ThemeSettings
from shuup.xtheme.testing import override_current_theme_class


@pytest.mark.django_db
def test_product_detail(client):
    shop = factories.get_default_shop()
    product = factories.create_product("sku", shop=shop, default_price=30)
    shop_product = product.get_shop_instance(shop)

    # Activate show supplier info for front
    assert ThemeSettings.objects.count() == 1
    theme_settings = ThemeSettings.objects.first()
    theme_settings.update_settings({"show_supplier_info": True})

    supplier_data = [
        ("Johnny Inc", 30),
        ("Mike Inc", 20),
        ("Simon Inc", 10),
    ]
    for name, product_price in supplier_data:
        supplier = Supplier.objects.create(name=name)
        supplier.shops.add(shop)
        shop_product.suppliers.add(supplier)
        SupplierPrice.objects.create(supplier=supplier, shop=shop, product=product, amount_value=product_price)

    strategy = "shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy"
    with override_settings(SHUUP_PRICING_MODULE="supplier_pricing", SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY=strategy):

        # Ok so cheapest price should be default supplier
        expected_supplier = shop_product.get_supplier()
        assert expected_supplier.name == "Simon Inc"
        with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
            soup = _get_product_detail_soup(client, product)

            _assert_supplier_subtitle(soup, expected_supplier)
            _assert_add_to_basket_form(soup, expected_supplier, 10)

            # Bonus! Let's say Johnny gets mad and starts to supply this product for 5 euros
            johnny_the_supplier = Supplier.objects.filter(name="Johnny Inc").first()
            SupplierPrice.objects.filter(supplier=johnny_the_supplier, shop=shop, product=product).update(
                amount_value=5
            )

            # This means that product detail get new default supplier and new price
            assert shop_product.get_supplier() == johnny_the_supplier
            soup = _get_product_detail_soup(client, product)

            _assert_supplier_subtitle(soup, johnny_the_supplier)
            _assert_add_to_basket_form(soup, johnny_the_supplier, 5)


@pytest.mark.django_db
def test_supplier_product_detail(client):
    shop = factories.get_default_shop()
    product = factories.create_product("sku", shop=shop, default_price=30)
    shop_product = product.get_shop_instance(shop)

    # Activate show supplier info for front
    assert ThemeSettings.objects.count() == 1
    theme_settings = ThemeSettings.objects.first()
    theme_settings.update_settings({"show_supplier_info": True})

    supplier_data = [
        ("Johnny Inc", 30),
        ("Mike Inc", 20),
        ("Simon Inc", 10),
    ]
    for name, product_price in supplier_data:
        supplier = Supplier.objects.create(name=name)
        supplier.shops.add(shop)
        shop_product.suppliers.add(supplier)
        SupplierPrice.objects.create(supplier=supplier, shop=shop, product=product, amount_value=product_price)

    strategy = "shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy"
    with override_settings(SHUUP_PRICING_MODULE="supplier_pricing", SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY=strategy):

        # Ok so cheapest price should be default supplier
        expected_supplier = shop_product.get_supplier()
        assert expected_supplier.name == "Simon Inc"
        with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
            johnny = Supplier.objects.filter(name="Johnny Inc").first()
            soup = _get_supplier_product_detail_soup(client, product, johnny)
            _assert_supplier_subtitle(soup, johnny)
            _assert_add_to_basket_form(soup, johnny, 30)

            mike = Supplier.objects.filter(name="Mike Inc").first()
            soup = _get_supplier_product_detail_soup(client, product, mike)
            _assert_supplier_subtitle(soup, mike)
            _assert_add_to_basket_form(soup, mike, 20)

            simon = Supplier.objects.filter(name="Simon Inc").first()
            soup = _get_supplier_product_detail_soup(client, product, simon)
            _assert_supplier_subtitle(soup, simon)
            _assert_add_to_basket_form(soup, simon, 10)


def _get_product_detail_soup(client, product):
    url = reverse("shuup:product", kwargs={"pk": product.pk, "slug": product.slug})
    response = client.get(url)
    return BeautifulSoup(response.content)


def _get_supplier_product_detail_soup(client, product, supplier):
    url = reverse("shuup:supplier-product", kwargs={"supplier_pk": supplier.pk, "pk": product.pk, "slug": product.slug})
    response = client.get(url)
    return BeautifulSoup(response.content)


def _assert_supplier_subtitle(soup, expected_supplier):
    supplier_subtitle = soup.find("p", {"class": "supplier-info"})
    assert supplier_subtitle
    assert expected_supplier.name in supplier_subtitle.text


def _assert_add_to_basket_form(soup, expected_supplier, expected_price_value):
    add_to_basket_form = soup.find("form", {"class": "add-to-basket"})
    supplier_input = add_to_basket_form.find("input", {"name": "supplier_id"})
    assert int(supplier_input["value"]) == expected_supplier.id
    product_price = add_to_basket_form.find("span", {"class": "product-price"})
    assert "%s" % expected_price_value in product_price.text
