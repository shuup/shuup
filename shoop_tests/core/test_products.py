# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from shoop.core.models import AnonymousContact, get_person_contact, ProductVisibility, Product
from shoop.testing.factories import get_default_shop_product
from shoop_tests.utils.fixtures import regular_user
from shoop_tests.core.utils import modify


@pytest.mark.django_db
@pytest.mark.usefixtures("regular_user")
def test_product_query(admin_user, regular_user):
    anon_contact = AnonymousContact()
    shop_product = get_default_shop_product()
    shop = shop_product.shop
    product = shop_product.product
    regular_contact = get_person_contact(regular_user)
    admin_contact = get_person_contact(admin_user)


    with modify(shop_product, save=True,
                listed=True,
                visible=True,
                visibility_limit=ProductVisibility.VISIBLE_TO_ALL
                ):
        assert Product.objects.list_visible(shop=shop, customer=anon_contact).filter(pk=product.pk).exists()

    with modify(shop_product, save=True,
                listed=False,
                visible=True,
                visibility_limit=ProductVisibility.VISIBLE_TO_ALL
                ):
        assert not Product.objects.list_visible(shop=shop, customer=anon_contact).filter(pk=product.pk).exists()
        assert not Product.objects.list_visible(shop=shop, customer=regular_contact).filter(pk=product.pk).exists()
        assert Product.objects.list_visible(shop=shop, customer=admin_contact).filter(pk=product.pk).exists()

    with modify(shop_product, save=True,
                listed=True,
                visible=True,
                visibility_limit=ProductVisibility.VISIBLE_TO_LOGGED_IN
                ):
        assert not Product.objects.list_visible(shop=shop, customer=anon_contact).filter(pk=product.pk).exists()
        assert Product.objects.list_visible(shop=shop, customer=regular_contact).filter(pk=product.pk).exists()

    product.soft_delete()
    assert not Product.objects.all_except_deleted().filter(pk=product.pk).exists()
