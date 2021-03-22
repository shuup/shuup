# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest
from bs4 import BeautifulSoup

from shuup.admin.modules.products.views import ProductEditView
from shuup.admin.modules.products.views.copy import ProductCopyView
from shuup.core.models import Product, ProductMedia, ProductMediaKind
from shuup.customer_group_pricing.models import CgpPrice
from shuup.simple_supplier.models import StockCount
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.utils.djangoenv import has_installed
from shuup_tests.simple_supplier.utils import get_simple_supplier


@pytest.mark.django_db
def test_copy_works_without_simple_supplier(rf, admin_user, settings):
    settings.INSTALLED_APPS.remove("shuup.simple_supplier")

    assert not has_installed("shuup.simple_supplier")
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    request = apply_request_middleware(rf.get("/", {}), user=admin_user)
    price = 10
    product = factories.create_product("product", shop=shop, supplier=supplier, default_price=price)

    shop_product = product.get_shop_instance(shop)

    assert Product.objects.count() == 1
    view_func = ProductCopyView.as_view()
    response = view_func(request, pk=shop_product.pk)
    if hasattr(response, "render"):
        response.render()

    assert Product.objects.count() == 2

    # Add back so rest of the tests work
    settings.INSTALLED_APPS.append("shuup.simple_supplier")


@pytest.mark.django_db
def test_product_copy_stock_managed(rf, admin_user):
    shop = factories.get_default_shop()
    supplier = get_simple_supplier()
    request = apply_request_middleware(rf.get("/", {}), user=admin_user)
    price = 10
    product = factories.create_product("product", shop=shop, supplier=supplier, default_price=price)

    shop_product = product.get_shop_instance(shop)

    assert Product.objects.count() == 1
    view_func = ProductCopyView.as_view()
    response = view_func(request, pk=shop_product.pk)
    if hasattr(response, "render"):
        response.render()

    assert Product.objects.count() == 2
    new_product = Product.objects.first()
    new_shop_product = new_product.get_shop_instance(shop)
    assert new_product
    assert new_product.pk != product.pk
    assert new_product.name == product.name
    assert new_shop_product
    assert new_shop_product.suppliers.first() == shop_product.suppliers.first()
    origin_product_stock_count = StockCount.objects.get_or_create(supplier=supplier, product=product)[0]
    new_product_stock_count = StockCount.objects.get_or_create(supplier=supplier, product=new_product)[0]
    assert origin_product_stock_count.stock_managed == new_product_stock_count.stock_managed

    # Make stock not managed and re-copy original product
    assert bool(origin_product_stock_count.stock_managed)  # stock managed True
    origin_product_stock_count.stock_managed = False
    origin_product_stock_count.save()

    assert Product.objects.count() == 2
    view_func = ProductCopyView.as_view()
    response = view_func(request, pk=shop_product.pk)
    if hasattr(response, "render"):
        response.render()

    assert Product.objects.count() == 3
    new_product = Product.objects.first()
    new_product_stock_count = StockCount.objects.get_or_create(supplier=supplier, product=new_product)[0]
    assert not bool(new_product_stock_count.stock_managed)


@pytest.mark.django_db
def test_product_copy_customer_group_pricing(rf, admin_user):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    request = apply_request_middleware(rf.get("/", {}), user=admin_user)
    price = 10
    product = factories.create_product("product", shop=shop, supplier=supplier, default_price=price)

    group = factories.get_default_customer_group()
    group_price_value = 9999
    CgpPrice.objects.create(product=product, shop=shop, group=group, price_value=group_price_value)
    shop_product = product.get_shop_instance(shop)

    assert Product.objects.count() == 1
    view_func = ProductCopyView.as_view()
    response = view_func(request, pk=shop_product.pk)
    if hasattr(response, "render"):
        response.render()

    assert Product.objects.count() == 2
    new_product = Product.objects.first()
    new_shop_product = new_product.get_shop_instance(shop)
    assert new_product
    assert new_product.pk != product.pk

    group_price = CgpPrice.objects.filter(product=new_product, shop=shop, group=group).first()
    assert group_price.price_value == group_price_value
