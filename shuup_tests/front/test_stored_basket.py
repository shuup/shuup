# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json

import pytest

from shuup.admin.shop_provider import set_shop
from shuup.core.models import get_person_contact
from shuup.front.admin_module.carts.views import (
    CartDetailView, CartListView
)
from shuup.front.basket import get_basket
from shuup.front.models import StoredBasket
from shuup.testing.factories import (
    create_product, get_default_payment_method, get_default_shipping_method,
    get_default_shop, get_shop, get_supplier
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.fixtures import regular_user


def _add_products_to_basket(basket, product_count):
    supplier = get_supplier("simple_supplier", basket.shop)
    for x in range(0, product_count):
        product = create_product(
            sku="%s-%s" % (printable_gibberish(), x),
            shop=basket.shop,
            supplier=supplier,
            default_price=50
        )
        basket.add_product(supplier=supplier, shop=basket.shop, product=product, quantity=1)

    return basket


def _create_cart_with_products(rf, shop, user, product_count):
    person = get_person_contact(user)
    get_default_payment_method()
    get_default_shipping_method()
    request = rf.post("/", {"title": "test"})
    request.shop = shop
    request.user = user
    request.person = person
    request.customer = person
    basket = get_basket(request)
    request = apply_request_middleware(request, user=user, person=person, customer=person, basket=basket)
    basket = _add_products_to_basket(basket, product_count)
    basket.save()
    return basket


@pytest.mark.django_db
@pytest.mark.parametrize("prices_include_taxes", (False, True))
def test_stored_basket_list_view(rf, regular_user, admin_user, prices_include_taxes):
    shop = get_shop(prices_include_tax=prices_include_taxes)
    cart1 = _create_cart_with_products(rf, shop, regular_user, 2)
    assert cart1
    assert cart1.product_count == 2
    assert cart1.taxful_total_price

    cart2 = _create_cart_with_products(rf, shop, regular_user, 0)
    assert cart2
    assert cart2.product_count == 0
    assert cart2.total_price == cart2.shop.create_price(0)

    # Normal HTMLResponse
    view = CartListView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
    set_shop(request, shop)
    response = view(request)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200

    # Fetching data and expecting JSONResponse
    view = CartListView.as_view()
    request = apply_request_middleware(rf.get("/", {
        "jq": json.dumps({"perPage": 100, "page": 1})
    }), user=admin_user, shop=shop)
    set_shop(request, shop)
    response = view(request)
    assert 200 <= response.status_code < 300

    data = json.loads(response.content.decode("utf-8"))
    assert len(data["items"]) == 2


@pytest.mark.django_db
def test_stored_basket_detail_view(rf, regular_user, admin_user):
    shop = get_default_shop()
    cart = _create_cart_with_products(rf, shop, regular_user, 2)
    assert cart
    assert cart.product_count == 2
    stored_basket = StoredBasket.objects.first()
    assert stored_basket and stored_basket.class_spec

    view = CartDetailView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
    set_shop(request, shop)
    response = view(request, pk=stored_basket.pk)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200

    stored_basket.class_spec = ""
    stored_basket.save()

    view = CartDetailView.as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user, shop=shop)
    set_shop(request, shop)
    response = view(request, pk=stored_basket.pk)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code == 200
