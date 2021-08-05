# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.signals import stocks_updated
from shuup.testing.factories import create_product, create_random_person, get_default_shop, get_default_supplier
from shuup.testing.receivers import shop_product_orderability_check


@pytest.mark.django_db
@pytest.mark.parametrize("hide_unorderable_product", [True, False])
def test_product_visibility_change_basic(hide_unorderable_product):
    """
    Make sure that the signal for hiding products when they become
    unorderable is called on shop product save.
    """
    if hide_unorderable_product:
        # Connect signal to hide products when they become unorderable
        stocks_updated.connect(receiver=shop_product_orderability_check, dispatch_uid="shop_product_orderability_check")

    shop = get_default_shop()
    contact = create_random_person()
    supplier = get_default_supplier()
    product = create_product("test", shop=shop, supplier=supplier, default_price=10)
    shop_product = product.get_shop_instance(shop=shop)
    assert shop_product.is_visible(contact)
    assert shop_product.is_purchasable(supplier, contact, 1)
    assert shop_product.is_orderable(supplier, contact, 1)

    shop_product.purchasable = False
    shop_product.save()
    supplier.update_stock(product.pk)
    shop_product.refresh_from_db()

    if hide_unorderable_product:
        assert not shop_product.is_visible(contact)
        assert not shop_product.is_purchasable(supplier, contact, 1)
        assert not shop_product.is_orderable(supplier, contact, 1)
        # Disconnect signal just in case...
        stocks_updated.disconnect(
            receiver=shop_product_orderability_check, dispatch_uid="shop_product_orderability_check"
        )
    else:
        assert shop_product.is_visible(contact)  # Still visible in front but not purchasable or orderable
        assert not shop_product.is_purchasable(supplier, contact, 1)
        assert not shop_product.is_orderable(supplier, contact, 1)
