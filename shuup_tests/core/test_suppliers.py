# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import Supplier
from shuup.testing.factories import (
    create_random_person,
    get_default_shop,
    get_default_shop_product,
    get_default_supplier,
)


@pytest.mark.django_db
def test_default_supplier():
    supplier = get_default_supplier()
    assert supplier.slug == supplier.name.lower()
    shop_product = get_default_shop_product()
    product = shop_product.product
    assert supplier.get_stock_statuses([product.id])[product.id].logical_count == 0
    assert not list(supplier.get_orderability_errors(shop_product, 1, customer=None))


@pytest.mark.django_db
def test_get_suppliable_products():
    customer = create_random_person()
    shop_product = get_default_shop_product()
    shop = get_default_shop()
    supplier = get_default_supplier()
    # Check for default orderable shop product with unstocked behavior
    assert len(list(supplier.get_suppliable_products(shop, customer=customer))) == 1

    supplier.stock_managed = True
    supplier.save()

    # Make sure supplier now omits unorderable product
    assert not list(supplier.get_suppliable_products(shop, customer=customer))
    assert len(list(supplier.get_orderability_errors(shop_product, quantity=1, customer=customer))) == 1

    shop_product.backorder_maximum = 10
    shop_product.save()

    assert len(list(supplier.get_suppliable_products(shop, customer=customer))) == 1
    assert len(list(supplier.get_orderability_errors(shop_product, quantity=10, customer=customer))) == 0
    assert len(list(supplier.get_orderability_errors(shop_product, quantity=11, customer=customer))) == 1

    shop_product.backorder_maximum = None
    shop_product.save()

    assert len(list(supplier.get_suppliable_products(shop, customer=customer))) == 1
    assert len(list(supplier.get_orderability_errors(shop_product, quantity=1000, customer=customer))) == 0


@pytest.mark.django_db
def test_suppliers_disabled():
    customer = create_random_person()
    shop_product = get_default_shop_product()
    shop = get_default_shop()
    supplier = get_default_supplier()

    assert shop_product.get_supplier() == supplier

    supplier.enabled = False
    supplier.save()
    assert shop_product.get_supplier() is None
    assert len(list(supplier.get_suppliable_products(shop, customer=customer))) == 0


@pytest.mark.django_db
def test_suppliers_queryset():
    supplier = get_default_supplier()
    assert Supplier.objects.enabled().count() == 1

    supplier.enabled = False
    supplier.save()
    assert Supplier.objects.enabled().count() == 0


@pytest.mark.django_db
def test_suppliers_deleted():
    supplier = get_default_supplier()
    supplier.soft_delete()
    assert supplier.deleted is True
