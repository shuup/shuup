# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.test.client import Client

from shuup.core.models import ShippingMode
from shuup.simple_supplier.module import SimpleSupplierModule
from shuup.testing import factories
from shuup.utils.django_compat import reverse


@pytest.mark.django_db
def test_reorder_view():
    shop = factories.get_default_shop()
    factories.get_default_shipping_method()
    factories.get_default_payment_method()

    supplier1 = factories.get_supplier(SimpleSupplierModule.identifier, shop=shop)
    supplier2 = factories.get_supplier(SimpleSupplierModule.identifier, shop=shop)
    assert supplier1.pk != supplier2.pk

    product_supplier1 = factories.create_product(
        "product_supplier1", shop=shop, supplier=supplier1, default_price=10, shipping_mode=ShippingMode.NOT_SHIPPED
    )
    product_supplier2 = factories.create_product(
        "product_supplier2", shop=shop, supplier=supplier2, default_price=20, shipping_mode=ShippingMode.NOT_SHIPPED
    )

    user = factories.create_random_user("en")
    user.set_password("user")
    user.save()

    customer = factories.create_random_person("en")
    customer.user = user
    customer.save()

    order = factories.create_random_order(
        customer=customer,
        shop=shop,
        products=[product_supplier1, product_supplier2],
        completion_probability=0,
        random_products=False,
    )
    suppliers = [line.supplier for line in order.lines.products()]
    assert supplier1 in suppliers
    assert supplier2 in suppliers

    client = Client()
    client.login(username=user.username, password="user")

    # list orders
    response = client.get(reverse("shuup:personal-orders"))
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "<td>%d</td>" % order.id in content
    assert "<td>Received</td>" in content

    # go to order detail
    response = client.get(reverse("shuup:show-order", kwargs=dict(pk=order.pk)))
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Add all products to cart" in content
    reorder_url = reverse("shuup:reorder-order", kwargs=dict(pk=order.pk))
    assert reorder_url in content

    # reorder products
    response = client.get(reorder_url)
    assert response.status_code == 302
    assert response.url.endswith(reverse("shuup:basket"))

    # go to basket
    response = client.get(response.url)
    assert response.status_code == 200
    content = response.content.decode("utf-8")

    # ensure the basket contain those products and suppliers
    basket_key = client.session["basket_basket_key"]["key"]
    from shuup.front.models import StoredBasket

    basket = StoredBasket.objects.get(key=basket_key)
    lines = basket.data["lines"]
    product_supplier = [(line["product_id"], line["supplier_id"]) for line in lines]
    assert (product_supplier1.pk, supplier1.pk) in product_supplier
    assert (product_supplier2.pk, supplier2.pk) in product_supplier

    assert product_supplier1.name in content
    assert product_supplier2.name in content
    assert "You are unable to proceed to checkout!" not in content
