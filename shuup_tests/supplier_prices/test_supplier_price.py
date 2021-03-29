# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.test import override_settings

from shuup.core.models import AnonymousContact, Supplier
from shuup.core.pricing import get_pricing_module
from shuup.testing import factories
from shuup.testing.models import SupplierPrice


@pytest.mark.django_db
def test_supplier_price_without_selected_supplier(rf):
    shop = factories.get_shop()

    supplier1 = Supplier.objects.create(name="Test 1")
    supplier1.shops.add(shop)
    supplier2 = Supplier.objects.create(name="Test 2")
    supplier2.shops.add(shop)

    strategy = "shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy"
    with override_settings(SHUUP_PRICING_MODULE="supplier_pricing", SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY=strategy):
        customer = AnonymousContact()
        pricing_mod = get_pricing_module()
        supplier1_ctx = pricing_mod.get_context_from_data(shop, customer, supplier=supplier1)
        supplier2_ctx = pricing_mod.get_context_from_data(shop, customer, supplier=supplier2)

        # Supplied by both suppliers
        product1_default_price = 10
        product1 = factories.create_product("sku1", shop=shop, supplier=supplier1, default_price=product1_default_price)
        shop_product1 = product1.get_shop_instance(shop)
        shop_product1.suppliers.add(supplier2)

        # Both suppliers should get price from shop
        # product default price
        assert product1.get_price(supplier1_ctx).amount.value == product1_default_price
        assert product1.get_price(supplier2_ctx).amount.value == product1_default_price

        # Now let's add per supplier prices
        supplier1_price = 7
        supplier2_price = 8
        SupplierPrice.objects.create(shop=shop, supplier=supplier1, product=product1, amount_value=supplier1_price)
        SupplierPrice.objects.create(shop=shop, supplier=supplier2, product=product1, amount_value=supplier2_price)

        assert product1.get_price(supplier1_ctx).amount.value == supplier1_price
        assert product1.get_price(supplier2_ctx).amount.value == supplier2_price

        # Now pricing context without defined supplier
        # should return cheapest price
        context = pricing_mod.get_context_from_data(shop, customer)
        assert shop_product1.get_supplier().pk == supplier1.pk
        assert product1.get_price(context).amount.value == supplier1_price
