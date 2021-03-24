# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import pytest
from bs4 import BeautifulSoup
from django.test import override_settings

from shuup.core.models import Supplier
from shuup.testing import factories
from shuup.testing.models import SupplierPrice
from shuup.utils.django_compat import reverse


@pytest.mark.django_db
def test_product_price(client):
    shop = factories.get_default_shop()
    product = factories.create_product("sku", shop=shop, default_price=30)
    shop_product = product.get_shop_instance(shop)

    supplier_data = [
        ("Johnny Inc", 30),
        ("Mike Inc", 20),
        ("Simon Inc", 10),
    ]
    for name, product_price in supplier_data:
        supplier = Supplier.objects.create(name=name)
        supplier.shops.add(shop)
        shop_product.suppliers.add(supplier)
        SupplierPrice.objects.create(supplier=supplier, shop=shop, product=product, amount_value=product_price)

    strategy = "shuup.testing.supplier_pricing.supplier_strategy:CheapestSupplierPriceSupplierStrategy"
    with override_settings(SHUUP_PRICING_MODULE="supplier_pricing", SHUUP_SHOP_PRODUCT_SUPPLIERS_STRATEGY=strategy):
        for name, price in supplier_data:
            supplier = Supplier.objects.get(name=name)
            response = client.get(
                reverse("shuup:xtheme_extra_view", kwargs={"view": "product_price"})
                + "?id=%s&quantity=%s&supplier=%s" % (product.pk, 1, supplier.pk)
            )
            soup = BeautifulSoup(response.content)
            price_span = soup.find("span", {"class": "product-price"})
            assert "%s" % price in price_span.text
