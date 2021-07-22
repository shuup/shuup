# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import Category, ProductType
from shuup.front.utils.sorts_and_filters import set_configuration
from shuup.testing import factories
from shuup.testing.factories import create_attribute_with_options
from shuup.utils.django_compat import reverse
from shuup_tests.utils import SmartClient


@pytest.mark.django_db
def test_product_price_range_filter(reindex_catalog):
    shop = factories.get_default_shop()
    product = factories.get_default_product()
    category = factories.get_default_category()
    shop_product = product.get_shop_instance(shop)
    shop_product.default_price_value = 10
    shop_product.save()
    shop_product.categories.add(category)
    reindex_catalog()

    client = SmartClient()
    config = {
        "filter_products_by_price": True,
        "filter_products_by_price_range_min": 5,
        "filter_products_by_price_range_max": 15,
        "filter_products_by_price_range_size": 5,
    }
    set_configuration(category=category, data=config)
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product.id)
    price_range_select = soup.find(id="id_price_range")
    # as the configuration is not set to override shop default configuration
    # this field shouldn't be there..
    assert price_range_select is None

    # make the category configuration override the shop's default config
    config.update({"override_default_configuration": True})
    set_configuration(category=category, data=config)
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product.id)
    price_range_select = soup.find(id="id_price_range")
    price_ranges = price_range_select.find_all("option")
    assert len(price_ranges) == 4

    # filter products with prices above $15
    filtered_url = "{}?price_range={}".format(url, price_ranges[-1].attrs["value"])
    response, soup = client.response_and_soup(filtered_url)
    assert response.status_code == 200
    assert not soup.find(id="product-%d" % product.id)

    # explicitly disable the override
    config.update({"override_default_configuration": False})
    set_configuration(category=category, data=config)
    url = reverse("shuup:category", kwargs={"pk": category.pk, "slug": category.slug})
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product.id)
    price_range_select = soup.find(id="id_price_range")
    assert price_range_select is None


@pytest.mark.django_db
def test_category_filter(reindex_catalog):
    shop = factories.get_default_shop()

    category1 = Category.objects.create(name="Category 1")
    category1.shops.add(shop)
    product1 = factories.create_product("p1", shop, factories.get_default_supplier(), "10")
    shop_product1 = product1.get_shop_instance(shop)
    shop_product1.categories.add(category1)

    category2 = Category.objects.create(name="Category 2")
    category2.shops.add(shop)
    product2 = factories.create_product("p2", shop, factories.get_default_supplier(), "20")
    shop_product2 = product2.get_shop_instance(shop)
    shop_product2.categories.add(category2)
    reindex_catalog()

    client = SmartClient()
    config = {"filter_products_by_category": True}
    set_configuration(shop=shop, data=config)

    url = reverse("shuup:all-categories")

    # 1) go to all categories view and list products
    # no filters being applied should list all products
    response, soup = client.response_and_soup(url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)

    # 2) filter by category2 id only
    response, soup = client.response_and_soup("{}?categories={}".format(url, category2.pk))
    assert response.status_code == 200
    assert not soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)

    # 3) filter by category1 and category2 id
    response, soup = client.response_and_soup("{}?categories={},{}".format(url, category1.pk, category2.pk))
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)

    # 4) filter by blank value, it shouldn't break
    response, soup = client.response_and_soup("{}?categories=".format(url))
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)


@pytest.mark.django_db
def test_product_attributes_filter(reindex_catalog):
    shop = factories.get_default_shop()

    category1 = Category.objects.create(name="Category 1")
    category1.shops.add(shop)
    product_type = ProductType.objects.create(name="Default Product Type")
    options_attribute = create_attribute_with_options("attribute1", ["A", "B", "C"], 1, 3)
    product_type.attributes.add(options_attribute)

    choices = list(options_attribute.choices.all().order_by("translations__name"))
    option_a, option_b, option_c = choices

    product1 = factories.create_product("p1", shop, factories.get_default_supplier(), "10", type=product_type)
    shop_product1 = product1.get_shop_instance(shop)
    shop_product1.categories.add(category1)
    product1.set_attribute_value("attribute1", [option_a.pk, option_c.pk])

    product2 = factories.create_product("p2", shop, factories.get_default_supplier(), "10", type=product_type)
    shop_product2 = product2.get_shop_instance(shop)
    shop_product2.categories.add(category1)
    product2.set_attribute_value("attribute1", [option_c.pk])

    reindex_catalog()

    client = SmartClient()
    config = {"filter_products_by_products_attribute": True, "override_default_configuration": True}
    set_configuration(category=category1, data=config)

    url = reverse("shuup:category", kwargs={"pk": category1.pk, "slug": category1.slug})
    filtered_url = "{}?attribute1={}".format(url, option_c.pk)
    response, soup = client.response_and_soup(filtered_url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product1.id)
    assert soup.find(id="product-%d" % product2.id)

    url = reverse("shuup:category", kwargs={"pk": category1.pk, "slug": category1.slug})
    filtered_url = "{}?attribute1={}".format(url, option_a.pk)
    response, soup = client.response_and_soup(filtered_url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product1.id)
    assert not soup.find(id="product-%d" % product2.id)

    url = reverse("shuup:category", kwargs={"pk": category1.pk, "slug": category1.slug})
    filtered_url = "{}?attribute1={}".format(url, option_b.pk)
    response, soup = client.response_and_soup(filtered_url)
    assert response.status_code == 200
    assert not soup.find(id="product-%d" % product1.id)
    assert not soup.find(id="product-%d" % product2.id)

    # Check category setting doesn't override
    config = {"filter_products_by_products_attribute": True, "override_default_configuration": False}
    set_configuration(category=category1, data=config)
    url = reverse("shuup:category", kwargs={"pk": category1.pk, "slug": category1.slug})
    filtered_url = "{}?attribute1={}".format(url, option_a.pk)
    response, soup = client.response_and_soup(filtered_url)
    assert response.status_code == 200
    assert soup.find(id="product-%d" % product2.id)

    # Check shop setting is working
    config = {
        "filter_products_by_products_attribute": True,
    }
    set_configuration(shop=shop, data=config)
    url = reverse("shuup:category", kwargs={"pk": category1.pk, "slug": category1.slug})
    filtered_url = "{}?attribute1={}".format(url, option_a.pk)
    response, soup = client.response_and_soup(filtered_url)
    assert response.status_code == 200
    assert not soup.find(id="product-%d" % product2.id)
