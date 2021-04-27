# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest

from shuup.admin.modules.products.mass_actions import InvisibleMassAction
from shuup.admin.modules.products.views import ProductListView, ProductMassEditView
from shuup.core.models import Product, ShopProductVisibility
from shuup.testing.factories import create_product, get_default_category, get_default_shop, get_default_supplier
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_mass_edit_products(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="501")

    category = get_default_category()
    shop_product1 = product1.get_shop_instance(shop)
    shop_product2 = product2.get_shop_instance(shop)

    # ensure no categories set
    assert shop_product1.primary_category is None
    assert shop_product2.primary_category is None

    request = apply_request_middleware(
        rf.post("/", data={"primary_category": category.pk, "categories": [category.pk]}), user=admin_user
    )
    request.session["mass_action_ids"] = [shop_product1.pk, shop_product2.pk]

    view = ProductMassEditView.as_view()
    response = view(request=request)
    assert response.status_code == 302
    for product in Product.objects.all():
        assert product.get_shop_instance(shop).primary_category == category
        assert product.get_shop_instance(shop).categories.first() == category


@pytest.mark.django_db
def test_mass_edit_products2(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="501")

    shop_product1 = product1.get_shop_instance(shop)
    shop_product2 = product2.get_shop_instance(shop)

    # ensure no categories set
    assert shop_product1.primary_category is None
    assert shop_product2.primary_category is None
    payload = {"action": InvisibleMassAction().identifier, "values": [shop_product1.pk, shop_product2.pk]}
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    request._body = json.dumps(payload).encode("UTF-8")
    view = ProductListView.as_view()
    response = view(request=request)
    assert response.status_code == 200
    for product in Product.objects.all():
        assert product.get_shop_instance(shop).visibility == ShopProductVisibility.NOT_VISIBLE
