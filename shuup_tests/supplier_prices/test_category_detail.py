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
from shuup.front.utils.sorts_and_filters import set_configuration
from shuup.testing import factories
from shuup.testing.models import SupplierPrice
from shuup.themes.classic_gray.theme import ClassicGrayTheme
from shuup.utils.django_compat import reverse
from shuup.xtheme.models import ThemeSettings
from shuup.xtheme.testing import override_current_theme_class


@pytest.mark.django_db
def test_category_detail(client, reindex_catalog):
    shop = factories.get_default_shop()

    # Activate show supplier info for front
    assert ThemeSettings.objects.count() == 1
    theme_settings = ThemeSettings.objects.first()
    theme_settings.update_settings({"show_supplier_info": True})

    # Activate supplier filters to prove they don't effect results
    # without actually filtering something. There is separate tests
    # to do the more closer tests.
    set_configuration(
        shop=shop,
        data={
            "filter_products_by_supplier": True,
            "filter_products_by_supplier_ordering": 1,
        },
    )

    category = factories.get_default_category()

    product_data = [("laptop", 1500), ("keyboard", 150), ("mouse", 150)]
    products = []
    for sku, price_value in product_data:
        products.append(factories.create_product(sku, shop=shop, default_price=price_value))

    supplier_data = [
        ("Johnny Inc", 0.5),
        ("Mike Inc", 0.9),
        ("Simon Inc", 0.8),
    ]
    for name, percentage_from_original_price in supplier_data:
        supplier = factories.get_supplier("simple_supplier", shop, name=name)

        for product in products:
            shop_product = product.get_shop_instance(shop)
            shop_product.suppliers.add(supplier)
            shop_product.primary_category = category
            shop_product.save()

            supplier_price = (
                percentage_from_original_price * [price for sku, price in product_data if product.sku == sku][0]
            )
            SupplierPrice.objects.create(supplier=supplier, shop=shop, product=product, amount_value=supplier_price)

    strategy = "shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy"
    with override_settings(SHUUP_PRICING_MODULE="supplier_pricing", SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY=strategy):
        with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
            reindex_catalog()

            soup = _get_category_detail_soup(client, category)

            # Johnny Inc has the best prices for everything
            laptop = [product for product in products if product.sku == "laptop"][0]
            laptop_product_box = soup.find("div", {"id": "product-%s" % laptop.pk})
            _assert_supplier_info(laptop_product_box, "Johnny Inc")
            _assert_product_price(laptop_product_box, 750)

            keyboard = [product for product in products if product.sku == "keyboard"][0]
            keyboard_product_box = soup.find("div", {"id": "product-%s" % keyboard.pk})
            _assert_supplier_info(keyboard_product_box, "Johnny Inc")
            _assert_product_price(keyboard_product_box, 75)

            mouse = [product for product in products if product.sku == "mouse"][0]
            mouse_product_box = soup.find("div", {"id": "product-%s" % mouse.pk})
            _assert_supplier_info(mouse_product_box, "Johnny Inc")
            _assert_product_price(mouse_product_box, 75)

            # Ok competition has done it job and the other suppliers
            # has to start adjust their prices.

            # Let's say Mike has the cheapest laptop
            mike_supplier = Supplier.objects.get(name="Mike Inc")
            SupplierPrice.objects.filter(supplier=mike_supplier, shop=shop, product=laptop).update(amount_value=333)
            reindex_catalog()

            soup = _get_category_detail_soup(client, category)
            laptop_product_box = soup.find("div", {"id": "product-%s" % laptop.pk})
            _assert_supplier_info(laptop_product_box, "Mike Inc")
            _assert_product_price(laptop_product_box, 333)

            # Just to make sure Simon takes over the mouse biz
            simon_supplier = Supplier.objects.get(name="Simon Inc")
            SupplierPrice.objects.filter(supplier=simon_supplier, shop=shop, product=mouse).update(amount_value=1)
            reindex_catalog()

            soup = _get_category_detail_soup(client, category)
            mouse_product_box = soup.find("div", {"id": "product-%s" % mouse.pk})
            _assert_supplier_info(mouse_product_box, "Simon Inc")
            _assert_product_price(mouse_product_box, 1)


def _get_category_detail_soup(client, category):
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    response = client.get(url)
    return BeautifulSoup(response.content, "lxml")


def _assert_supplier_info(box_soup, expected_supplier_name):
    supplier_info_soup = box_soup.find("p", {"class": "supplier-info"})
    assert expected_supplier_name in supplier_info_soup.text


def _assert_product_price(box_soup, expected_price_value):
    price_line_soup = box_soup.find("div", {"class": "price-line"})
    assert "%s" % expected_price_value in price_line_soup.text
