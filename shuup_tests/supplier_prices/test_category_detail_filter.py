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
from shuup.front.forms.product_list_supplier_modifier import SupplierProductListFilter
from shuup.front.utils.sorts_and_filters import set_configuration
from shuup.testing import factories
from shuup.testing.models import SupplierPrice
from shuup.testing.utils import apply_request_middleware
from shuup.themes.classic_gray.theme import ClassicGrayTheme
from shuup.utils.django_compat import reverse
from shuup.xtheme.models import ThemeSettings
from shuup.xtheme.testing import override_current_theme_class


@pytest.mark.django_db
def test_supplier_filter_get_fields(rf, reindex_catalog):
    shop = factories.get_default_shop()
    request = apply_request_middleware(rf.get("/"))
    category = factories.get_default_category()

    supplier = Supplier.objects.create(name="Mike Inc")
    supplier.shops.add(shop)
    assert SupplierProductListFilter().get_fields(request, None) is None

    product = factories.create_product("sku", shop=shop)
    shop_product = product.get_shop_instance(shop=shop)
    shop_product.primary_category = category
    shop_product.save()
    reindex_catalog()

    assert SupplierProductListFilter().get_fields(request, category) is None

    # Now once we link manufacturer to product we should get
    # form field for manufacturer
    shop_product.suppliers.add(supplier)
    form_field = SupplierProductListFilter().get_fields(request, category)[0][1]
    assert form_field is not None
    assert form_field.label == "Suppliers"
    assert len(form_field.widget.choices) == 1

    # Add second supplier for new product
    supplier2 = Supplier.objects.create(name="K Inc")
    supplier2.shops.add(shop)
    new_product = factories.create_product("sku1", shop=shop)
    new_shop_product = new_product.get_shop_instance(shop=shop)
    new_shop_product.suppliers.add(supplier2)

    # Still one with category since shop product not linked to category
    form_field = SupplierProductListFilter().get_fields(request, category)[0][1]
    assert form_field is not None
    assert len(form_field.widget.choices) == 1

    # Without category we get two results
    form_field = SupplierProductListFilter().get_fields(request, None)[0][1]
    assert form_field is not None
    assert len(form_field.widget.choices) == 2

    new_shop_product.categories.add(category)  # primary category shouldn't be required

    # Now with or without category we get 2 results
    form_field = SupplierProductListFilter().get_fields(request, category)[0][1]
    assert form_field is not None
    assert len(form_field.widget.choices) == 2

    form_field = SupplierProductListFilter().get_fields(request, None)[0][1]
    assert form_field is not None
    assert len(form_field.widget.choices) == 2


@pytest.mark.django_db
def test_category_detail_filters(client, reindex_catalog):
    shop = factories.get_default_shop()

    # Activate show supplier info for front
    assert ThemeSettings.objects.count() == 1
    theme_settings = ThemeSettings.objects.first()
    theme_settings.update_settings({"show_supplier_info": True})

    category = factories.get_default_category()

    # Important! Activate supplier filter.
    set_configuration(
        shop=shop,
        data={
            "filter_products_by_supplier": True,
            "filter_products_by_supplier_ordering": 1,
        },
    )

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
            shop_product.categories.add(category)
            shop_product.save()

            supplier_price = (
                percentage_from_original_price * [price for sku, price in product_data if product.sku == sku][0]
            )
            SupplierPrice.objects.create(supplier=supplier, shop=shop, product=product, amount_value=supplier_price)

    strategy = "shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy"
    with override_settings(SHUUP_PRICING_MODULE="supplier_pricing", SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY=strategy):
        with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
            reindex_catalog()

            laptop = [product for product in products if product.sku == "laptop"][0]
            keyboard = [product for product in products if product.sku == "keyboard"][0]
            mouse = [product for product in products if product.sku == "mouse"][0]
            # Let's get products for Johnny
            supplier_johnny = Supplier.objects.filter(name="Johnny Inc").first()
            soup = _get_category_detail_soup(client, category, supplier_johnny.pk)

            laptop_product_box = soup.find("div", {"id": "product-%s" % laptop.pk})
            _assert_supplier_info(laptop_product_box, "Johnny Inc")
            _assert_product_price(laptop_product_box, 750)

            # Now here when the category view is filtered based on supplier
            # the product urls should lead to supplier product url so we
            # can show details and prices for correct supplier.
            _assert_product_url(laptop_product_box, supplier_johnny, laptop)

            # Let's test rest of the products and suppliers
            keyboard_product_box = soup.find("div", {"id": "product-%s" % keyboard.pk})
            _assert_supplier_info(keyboard_product_box, "Johnny Inc")
            _assert_product_price(keyboard_product_box, 75)
            _assert_product_url(keyboard_product_box, supplier_johnny, keyboard)

            mike_supplier = Supplier.objects.filter(name="Mike Inc").first()
            soup = _get_category_detail_soup(client, category, mike_supplier.pk)
            keyboard_product_box = soup.find("div", {"id": "product-%s" % keyboard.pk})
            _assert_supplier_info(keyboard_product_box, "Mike Inc")
            _assert_product_price(keyboard_product_box, 135)
            _assert_product_url(keyboard_product_box, mike_supplier, keyboard)

            simon_supplier = Supplier.objects.filter(name="Simon Inc").first()
            soup = _get_category_detail_soup(client, category, simon_supplier.pk)
            mouse_product_box = soup.find("div", {"id": "product-%s" % mouse.pk})
            _assert_supplier_info(mouse_product_box, "Simon Inc")
            _assert_product_price(mouse_product_box, 120)
            _assert_product_url(mouse_product_box, simon_supplier, mouse)


@pytest.mark.django_db
def test_category_detail_multiselect_supplier_filters(client, reindex_catalog):
    shop = factories.get_default_shop()

    # Activate show supplier info for front
    assert ThemeSettings.objects.count() == 1
    theme_settings = ThemeSettings.objects.first()
    theme_settings.update_settings({"show_supplier_info": True})

    category = factories.get_default_category()

    # Important! Activate supplier filter.
    set_configuration(
        shop=shop,
        data={
            "filter_products_by_supplier": True,
            "filter_products_by_supplier_ordering": 1,
            "filter_products_by_supplier_multiselect_enabled": True,
        },
    )

    supplier_data = [
        ("Johnny Inc", 0.5),
        ("Mike Inc", 0.9),
        ("Simon Inc", 0.8),
    ]

    for name, percentage_from_original_price in supplier_data:
        supplier = factories.get_supplier("simple_supplier", shop, name=name)
        sku = name
        price_value = 10
        product = factories.create_product(sku, shop=shop, default_price=price_value)
        shop_product = product.get_shop_instance(shop)
        shop_product.suppliers.add(supplier)
        shop_product.primary_category = category
        shop_product.categories.add(category)
        shop_product.save()

        supplier_price = percentage_from_original_price * price_value
        SupplierPrice.objects.create(supplier=supplier, shop=shop, product=product, amount_value=supplier_price)

    reindex_catalog()

    strategy = "shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy"
    with override_settings(SHUUP_PRICING_MODULE="supplier_pricing", SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY=strategy):
        with override_current_theme_class(ClassicGrayTheme, shop):  # Ensure settings is refreshed from DB
            johnny_supplier = Supplier.objects.filter(name="Johnny Inc").first()
            mike_supplier = Supplier.objects.filter(name="Mike Inc").first()
            simon_supplier = Supplier.objects.filter(name="Simon Inc").first()

            soup = _get_category_detail_soup_multiselect(client, category, [johnny_supplier.pk])
            assert len(soup.findAll("div", {"class": "single-product"})) == 1

            soup = _get_category_detail_soup_multiselect(client, category, [johnny_supplier.pk, mike_supplier.pk])
            assert len(soup.findAll("div", {"class": "single-product"})) == 2

            soup = _get_category_detail_soup_multiselect(
                client, category, [johnny_supplier.pk, mike_supplier.pk, simon_supplier.pk]
            )
            assert len(soup.findAll("div", {"class": "single-product"})) == 3


def _get_category_detail_soup(client, category, supplier_id):
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    response = client.get(url, data={"supplier": supplier_id})
    return BeautifulSoup(response.content, "lxml")


def _get_category_detail_soup_multiselect(client, category, supplier_ids):
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    response = client.get(url, data={"suppliers": ",".join(["%s" % sid for sid in supplier_ids])})
    return BeautifulSoup(response.content, "lxml")


def _assert_supplier_info(box_soup, expected_supplier_name):
    supplier_info_soup = box_soup.find("p", {"class": "supplier-info"})
    assert expected_supplier_name in supplier_info_soup.text


def _assert_product_price(box_soup, expected_price_value):
    price_line_soup = box_soup.find("div", {"class": "price-line"})
    assert "%s" % expected_price_value in price_line_soup.text


def _assert_product_url(box_soup, supplier, product):
    expected_url = reverse(
        "shuup:supplier-product", kwargs={"supplier_pk": supplier.pk, "pk": product.pk, "slug": product.slug}
    )

    link = box_soup.find("a", {"rel": "product-detail"})
    assert expected_url in link["href"]
