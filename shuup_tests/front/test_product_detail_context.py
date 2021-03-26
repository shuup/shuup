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
from shuup.front.utils.product import get_product_context
from shuup.testing.factories import create_product, get_default_product, get_default_shop, get_default_supplier
from shuup.testing.utils import apply_request_middleware
from shuup.utils.django_compat import reverse
from shuup_tests import supplier_prices


@pytest.mark.django_db
def test_variation_product_price_more_complex(rf):
    shop = get_default_shop()
    supplier = get_default_supplier(shop)

    product_data = {
        "supplier-1": {
            "sizes": ["S", "M"],
            "colors": ["Black", "Yellow"],
        },
        "supplier-2": {
            "sizes": ["XL"],
            "colors": ["Yellow"],
        },
    }
    parent = create_product("ComplexVarParent", shop=shop)
    shop_parent_product = parent.get_shop_instance(shop)
    for key, data in six.iteritems(product_data):
        supplier = Supplier.objects.create(identifier=key)
        supplier.shops.add(shop)
        for size in data["sizes"]:
            for color in data["colors"]:
                sku = "ComplexVarChild-%s-%s" % (size, color)
                shop_product = ShopProduct.objects.filter(product__sku=sku).first()
                if shop_product:
                    shop_product.suppliers.add(supplier)
                else:
                    child = create_product(sku, shop=shop, supplier=supplier)
                    child.link_to_parent(parent, variables={"size": size, "color": color})

    assert parent.variation_children.count() == 5
    # We have 6 different combinations but only 5 combinations
    # has product in them.
    assert len(list(parent.get_all_available_combinations())) == 6

    request = apply_request_middleware(rf.get("/"))
    request.shop = shop

    supplier1 = Supplier.objects.get(identifier="supplier-1")
    # For cache
    for x in range(0, 1):
        context = get_product_context(request, parent, supplier=supplier1)
        assert len(context["orderable_variation_children"]) == 2
        for variation_variable, variable_values in six.iteritems(context["orderable_variation_children"]):
            assert len(variable_values) == 2

    supplier2 = Supplier.objects.get(identifier="supplier-2")
    # For cache
    for x in range(0, 1):
        context = get_product_context(request, parent, supplier=supplier2)
        assert len(context["orderable_variation_children"]) == 2
        for variation_variable, variable_values in six.iteritems(context["orderable_variation_children"]):
            assert len(variable_values) == 1
