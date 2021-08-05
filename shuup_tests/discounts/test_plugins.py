# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from datetime import timedelta
from django.utils.timezone import now

from shuup.core.models import CategoryStatus
from shuup.discounts.models import Discount
from shuup.discounts.plugins import DiscountedProductsPlugin
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.xtheme._theme import get_current_theme, override_current_theme_class
from shuup.xtheme.layout import LayoutCell
from shuup.xtheme.views.forms import LayoutCellFormGroup
from shuup_tests.front.fixtures import get_jinja_context


def get_context(rf, customer=None):
    request = rf.get("/")
    request.shop = factories.get_default_shop()
    apply_request_middleware(request)
    if customer:
        request.customer = customer
    return get_jinja_context(**{"request": request})


@pytest.mark.django_db
def test_product_selection_plugin(rf, reindex_catalog):
    shop = factories.get_default_shop()
    shop2 = factories.get_shop(identifier="shop2")
    category1 = factories.CategoryFactory(status=CategoryStatus.VISIBLE)
    category2 = factories.CategoryFactory(status=CategoryStatus.VISIBLE)

    p1 = factories.create_product("p1", shop, factories.get_default_supplier(), "10")
    p2 = factories.create_product("p2", shop, factories.get_default_supplier(), "20")
    p3 = factories.create_product("p3", shop, factories.get_default_supplier(), "30")
    p4 = factories.create_product("p4", shop, factories.get_default_supplier(), "40")
    p5 = factories.create_product("p5", shop, factories.get_default_supplier(), "50")

    sp1 = p1.get_shop_instance(shop)
    sp2 = p2.get_shop_instance(shop)
    sp3 = p3.get_shop_instance(shop)
    sp4 = p4.get_shop_instance(shop)

    sp1.categories.add(category1, category2)
    sp2.categories.add(category1)
    sp3.categories.add(category2)
    sp4.categories.add(category2)

    # this discount should show products: p1, p2 and p5
    discount1 = Discount.objects.create(
        shop=shop,
        name="discount1",
        active=True,
        start_datetime=now() - timedelta(days=10),
        end_datetime=now() + timedelta(days=1),
        product=p5,
        category=category1,
    )

    # this discount should show products: p1, p3 and p4
    discount2 = Discount.objects.create(
        shop=shop,
        name="discount2",
        active=True,
        start_datetime=now() - timedelta(days=10),
        end_datetime=now() + timedelta(days=1),
        category=category2,
    )

    # this discount shouldn't be available for this shop
    discount3 = Discount.objects.create(
        shop=shop2,
        name="discount3",
        active=True,
        start_datetime=now() - timedelta(days=10),
        end_datetime=now() + timedelta(days=1),
        category=category2,
    )

    reindex_catalog()
    context = get_context(rf)

    # test only discount1
    plugin = DiscountedProductsPlugin({"discounts": [discount1.pk], "count": 10})
    context_products = plugin.get_context_data(context)["products"]
    assert p1 in context_products
    assert p2 in context_products
    assert p3 not in context_products
    assert p4 not in context_products
    assert p5 in context_products

    for status in range(2):
        if status == 1:
            discount2.active = False
            discount2.save()
            reindex_catalog()

        # test only discount2
        plugin = DiscountedProductsPlugin({"discounts": [discount2.pk], "count": 10})
        context_products = plugin.get_context_data(context)["products"]

        if status == 1:
            assert list(context_products) == []
        else:
            assert p1 in context_products
            assert p2 not in context_products
            assert p3 in context_products
            assert p4 in context_products
            assert p5 not in context_products

    # test discount3
    plugin = DiscountedProductsPlugin({"discounts": [discount3.pk], "count": 10})
    assert list(plugin.get_context_data(context)["products"]) == []

    discount2.active = True
    discount2.save()
    reindex_catalog()

    # test both discount1 and discount2
    plugin = DiscountedProductsPlugin({"discounts": [discount1.pk, discount2.pk], "count": 10})
    context_products = plugin.get_context_data(context)["products"]
    assert p1 in context_products
    assert p2 in context_products
    assert p3 in context_products
    assert p4 in context_products
    assert p5 in context_products

    # test the plugin form
    with override_current_theme_class(None):
        theme = get_current_theme(shop)
        cell = LayoutCell(theme, DiscountedProductsPlugin.identifier, sizes={"md": 8})
        lcfg = LayoutCellFormGroup(layout_cell=cell, theme=theme, request=apply_request_middleware(rf.get("/")))
        # not valid, products are required
        assert not lcfg.is_valid()

        lcfg = LayoutCellFormGroup(
            data={
                "general-cell_width": "8",
                "general-cell_align": "pull-right",
                "plugin-discounts": [discount1.pk, discount2.pk],
                "plugin-count": 6,
            },
            layout_cell=cell,
            theme=theme,
            request=apply_request_middleware(rf.get("/")),
        )
        assert lcfg.is_valid()
        lcfg.save()
        assert cell.config["discounts"] == [discount1.pk, discount2.pk]
