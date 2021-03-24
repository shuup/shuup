# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
import six
from decimal import Decimal

from shuup.core.models import Product, ShopProduct, Supplier
from shuup.front.themes.views._product_price import ProductPriceView
from shuup.testing.factories import create_product, get_default_product, get_default_shop, get_default_supplier
from shuup.utils.django_compat import reverse


@pytest.mark.django_db
def test_product_price(client):
    shop = get_default_shop()
    product = get_default_product()
    response = client.get(
        reverse("shuup:xtheme_extra_view", kwargs={"view": "product_price"}) + "?id=%s&quantity=%s" % (product.pk, 1)
    )
    assert response.context_data["product"] == product
    assert b"form" in response.content


@pytest.mark.django_db
def test_product_price_without_shop_product(client):
    shop = get_default_shop()
    product = get_default_product()
    response = client.get(
        reverse("shuup:xtheme_extra_view", kwargs={"view": "product_price"}) + "?id=%s" % (product.pk)
    )
    assert response.context_data["product"] == product
    assert "Combination not available" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_variation_product_price_simple(client):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("Parent", supplier=supplier, shop=shop, default_price="10")
    child = create_product("SimpleVarChild", supplier=supplier, shop=shop, default_price="5")
    child.link_to_parent(product, variables={"size": "S"})
    response = client.get(
        reverse("shuup:xtheme_extra_view", kwargs={"view": "product_price"})
        + "?id=%s&quantity=%s&var_1=1" % (product.pk, 1)
    )
    assert response.context_data["product"] == child
    assert b"form" in response.content

    sp = child.get_shop_instance(shop)
    sp.suppliers.remove(supplier)
    response = client.get(
        reverse("shuup:xtheme_extra_view", kwargs={"view": "product_price"})
        + "?id=%s&quantity=%s&var_1=1" % (product.pk, 1)
    )
    assert response.context_data["product"] == child
    # product isn't orderable since no supplier
    assert b"no-price" in response.content


@pytest.mark.django_db
def test_variation_product_price_more_complex(client):
    shop = get_default_shop()
    supplier = get_default_supplier(shop)

    product_data = {
        "supplier-1": {
            "sizes": ["S", "M", "XL"],
            "colors": ["Black", "Yellow", "Blue"],
            "material": ["leather", "cotton"],
        },
        "supplier-2": {"sizes": ["S", "XL", "XS", "XXL", "M"], "colors": ["Yellow", "Red"], "material": ["cotton"]},
    }
    parent = create_product("ComplexVarParent", shop=shop)
    shop_parent_product = parent.get_shop_instance(shop)
    for key, data in six.iteritems(product_data):
        supplier = Supplier.objects.create(identifier=key)
        supplier.shops.add(shop)
        for size in data["sizes"]:
            for color in data["colors"]:
                for material in data["material"]:
                    sku = "ComplexVarChild-%s-%s-%s" % (size, color, material)
                    shop_product = ShopProduct.objects.filter(product__sku=sku).first()
                    if shop_product:
                        shop_product.suppliers.add(supplier)
                    else:
                        child = create_product(sku, shop=shop, supplier=supplier)
                        child.link_to_parent(parent, variables={"size": size, "color": color, "material": material})

    assert parent.variation_children.count() == 25
    # We have 6 different combinations but only 5 combinations
    # has product in them.
    assert len(list(parent.get_all_available_combinations())) == 40

    # Lets test prices for suppliers
    for key, data in six.iteritems(product_data):
        supplier_id = Supplier.objects.get(identifier=key).id
        available_combinations = set()
        for size in data["sizes"]:
            for color in data["colors"]:
                for material in data["material"]:
                    available_combinations.add("color: %s, material: %s, size: %s" % (color, material, size))

        expected_orderable_count = len(available_combinations)
        actual_orderable_count = 0
        had_at_least_one_not_orderable_in_this_test = False
        for combination in parent.get_all_available_combinations():
            product_result_pk = combination["result_product_pk"]
            status_code = 200
            if not product_result_pk:  # we can skip combinations without products
                status_code = 404

            variable_string = ""
            for key, value in six.iteritems(combination["variable_to_value"]):
                variable_string += "var_%s=%s&" % (key.pk, value.pk)

            response = client.get(
                reverse("shuup:xtheme_extra_view", kwargs={"view": "product_price"})
                + "?id=%s&quantity=%s&%ssupplier=%s" % (parent.pk, 1, variable_string, supplier_id)
            )
            assert response.status_code == status_code
            if not status_code == 404:
                assert response.context_data["product"] == Product.objects.filter(id=product_result_pk).first()
                content = response.content.decode("utf-8")

                is_orderable = combination["text_description"] in available_combinations
                if is_orderable:
                    actual_orderable_count += 1
                    assert "form" in content
                else:
                    had_at_least_one_not_orderable_in_this_test = True
                    assert "Combination not available" in content

        assert actual_orderable_count == expected_orderable_count
        assert had_at_least_one_not_orderable_in_this_test


def test_product_price_get_quantity(rf):
    shop = get_default_shop()
    product = create_product("sku", shop=shop)
    shop_product = product.get_shop_instance(shop)

    view = ProductPriceView()
    view.request = rf.get("/")
    assert "quantity" not in view.request.GET

    def check(shop_product, input_value, expected_output):
        view.request.GET = dict(view.request.GET, quantity=input_value)
        result = view._get_quantity(shop_product)
        if expected_output is None:
            assert result is None
        else:
            assert isinstance(result, Decimal)
            assert result == expected_output

    check(shop_product, "42", 42)
    check(shop_product, "1.5", Decimal("1.5"))
    check(shop_product, "3.2441", Decimal("3.2441"))
    check(shop_product, "0.0000000001", Decimal("0.0000000001"))
    check(shop_product, "0.000000000001", Decimal("0.000000000001"))
    check(shop_product, "123456789123456789123456789", 123456789123456789123456789)
    check(shop_product, "0", 0)
    check(shop_product, "-100", None)
    check(shop_product, "", None)
    check(shop_product, "inf", None)
    check(shop_product, "nan", None)
    check(shop_product, "Hello", None)
    check(shop_product, "1.2.3", None)
    check(shop_product, "1.2.3.4", None)
    check(shop_product, "1-2", None)
    check(shop_product, "1 2 3", None)
    check(shop_product, "1e30", None)
    check(shop_product, "1,5", None)
    check(shop_product, "mämmi", None)
    check(shop_product, "3€", None)
    check(shop_product, "\0", None)
    check(shop_product, "123\0", None)
    check(shop_product, "123\0456", None)
    check(shop_product, "\n", None)


@pytest.mark.parametrize("decimals", [0, 2])
def test_product_price_get_quantity_with_display_unit(rf, decimals):
    shop = get_default_shop()
    product = create_product("sku", shop=shop)
    shop_product = product.get_shop_instance(shop)
    from shuup.core.models import DisplayUnit, SalesUnit

    sales_unit = SalesUnit.objects.create(identifier="random", decimals=decimals)
    product.sales_unit = sales_unit
    product.save()

    view = ProductPriceView()
    view.request = rf.get("/")
    assert "quantity" not in view.request.GET

    def check(shop_product, input_value, expected_output):
        view.request.GET = dict(view.request.GET, quantity=input_value, unitType="not internal")
        result = view._get_quantity(shop_product)
        assert result == expected_output

    if not decimals:
        check(shop_product, "42.232323", 42)
    else:
        check(shop_product, "42.23232323", Decimal("42.23"))
