# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from shuup.core.models import Product
from shuup.core.utils.product_caching_object import ProductCachingObject
from shuup.testing.factories import create_product, get_default_category, get_default_shop_product


def test_product_caching_object_nulling():
    pco = ProductCachingObject()
    pco.product = None
    assert not pco.product
    assert not pco.product_id

    pco = ProductCachingObject()
    pco.product = None
    assert not pco.product_id

    pco = ProductCachingObject()
    pco.product_id = None
    assert not pco.product


def test_product_caching_object_type_validation():
    with pytest.raises(TypeError):
        pco = ProductCachingObject()
        pco.product_id = "yeah"

    with pytest.raises(TypeError):
        pco = ProductCachingObject()
        pco.product = "yeahhh"

    with pytest.raises(ValueError):
        pco = ProductCachingObject()
        pco.product = Product()


@pytest.mark.django_db
def test_product_caching_object():
    shop_product = get_default_shop_product()
    product = shop_product.product
    another_product = create_product("PCOTestProduct")

    pco = ProductCachingObject()
    pco.product = product
    assert pco.product is product
    assert pco.product_id == product.pk
    assert ProductCachingObject().product != pco.product  # Assert PCOs are separate
    assert pco._product_cache == pco.product  # This private property is courtesy of ModelCachingDescriptor

    pco = ProductCachingObject()
    pco.product_id = product.pk
    assert pco.product == product
    assert pco.product_id == product.pk

    # Not creating a new PCO here
    pco.product = another_product
    assert pco.product == another_product
    assert pco.product_id == another_product.pk

    # Nor here
    pco.product_id = product.pk
    assert pco.product == product
    assert pco.product_id == product.pk


@pytest.mark.django_db
def test_shopproduct_categories_manytomany():
    shop_product = get_default_shop_product()
    category = get_default_category()
    shop_product.categories.set([category])
    assert shop_product.categories.first() == category
    assert category.shop_products.first() == shop_product


@pytest.mark.django_db
def test_categories_shopproducts_manytomany():
    shop_product = get_default_shop_product()
    category = get_default_category()
    category.shop_products.set([shop_product])
    assert category.shop_products.first() == shop_product
    assert shop_product.categories.first() == category
