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
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_copy_url_at_edit_view(rf, admin_user):
    shop = factories.get_default_shop()
    request = apply_request_middleware(rf.get("/", {}), user=admin_user)
    product = factories.create_product("product", shop=shop)
    shop_product = product.get_shop_instance(shop)

    view_func = ProductEditView.as_view()
    response = view_func(request, pk=shop_product.pk)
    if hasattr(response, "render"):
        response.render()

    soup = BeautifulSoup(response.content)

    expected_url = "/sa/products/%s/copy/" % shop_product.pk
    assert len(soup.findAll("a", {"href": expected_url})) == 1


@pytest.mark.django_db
def test_product_copy(rf, admin_user):
    factories.get_default_attribute_set()
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    request = apply_request_middleware(rf.get("/", {}), user=admin_user)
    price = 10
    product = factories.create_product("product", shop=shop, supplier=supplier, default_price=price)

    attribute_key = "author"
    attribute_value = "batman"
    product.set_attribute_value(attribute_key, attribute_value)

    media = ProductMedia.objects.create(
        product=product, kind=ProductMediaKind.IMAGE, file=factories.get_random_filer_image(), enabled=True, public=True
    )
    product.primary_image = media
    product.media.add(media)
    product.save()

    category = factories.get_default_category()
    shop_product = product.get_shop_instance(shop)
    shop_product.primary_category = category
    shop_product.save()
    shop_product.categories.set([category])

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
    assert new_shop_product.categories.first() == shop_product.categories.first()
    assert new_product.media.first().file.pk == product.media.first().file.pk
    assert new_product.get_attribute_value(attribute_key) == attribute_value
