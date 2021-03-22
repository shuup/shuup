# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest

from shuup.core.models import get_person_contact
from shuup.front.apps.saved_carts.views import (
    CartAddAllProductsView,
    CartDeleteView,
    CartDetailView,
    CartListView,
    CartSaveView,
)
from shuup.front.basket import get_basket
from shuup.front.models import StoredBasket
from shuup.testing.factories import (
    create_product,
    get_default_payment_method,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.fixtures import regular_user


def _add_products_to_basket(basket):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=2)
    assert basket.product_count, "basket has products"
    return basket


def _save_cart_with_products(rf, user):
    shop = get_default_shop()
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
    basket = _add_products_to_basket(basket)
    basket.save()
    response = CartSaveView.as_view()(request)
    basket = StoredBasket.objects.filter(title="test").first()
    data = json.loads(response.content.decode("utf8"))
    assert data["ok"], "cart saved successfully"
    return basket


@pytest.mark.django_db
def test_save_cart_errors(rf, regular_user):
    get_default_shop()
    request = apply_request_middleware(rf.post("/", {"title": "test"}))
    response = CartSaveView.as_view()(request)
    data = json.loads(response.content.decode("utf8"))
    assert response.status_code == 403, "can't save cart as anonymous user"
    assert not data["ok"], "can't save cart without title"

    customer = get_person_contact(regular_user)
    request = apply_request_middleware(rf.post("/", {"title": ""}), customer=customer, user=regular_user)
    response = CartSaveView.as_view()(request)
    data = json.loads(response.content.decode("utf8"))
    assert response.status_code == 400
    assert not data["ok"], "can't save cart without title"

    request = apply_request_middleware(rf.post("/", {"title": "test"}), customer=customer, user=regular_user)
    response = CartSaveView.as_view()(request)
    data = json.loads(response.content.decode("utf8"))
    assert response.status_code == 400
    assert not data["ok"], "can't save an empty cart"


@pytest.mark.django_db
def test_save_cart(rf, regular_user):
    cart = _save_cart_with_products(rf, regular_user)
    assert cart
    assert cart.product_count == 2


@pytest.mark.django_db
def test_cart_list(rf, regular_user):
    _save_cart_with_products(rf, regular_user)
    request = apply_request_middleware(rf.get("/"), customer=get_person_contact(regular_user), user=regular_user)
    response = CartListView.as_view()(request)
    assert response.status_code == 200
    assert "carts" in response.context_data
    assert response.context_data["carts"].count() == 1


@pytest.mark.django_db
def test_cart_detail(rf, regular_user):
    cart = _save_cart_with_products(rf, regular_user)
    request = apply_request_middleware(rf.get("/"), customer=get_person_contact(regular_user), user=regular_user)
    response = CartDetailView.as_view()(request, pk=cart.pk)
    assert response.status_code == 200
    assert "cart" in response.context_data
    assert response.context_data["cart"].products.count() == 1
    assert "lines" in response.context_data
    assert len(response.context_data["lines"]) == 1


@pytest.mark.django_db
def test_cart_delete(rf, regular_user):
    cart = _save_cart_with_products(rf, regular_user)
    request = apply_request_middleware(rf.post("/"), customer=get_person_contact(regular_user), user=regular_user)
    response = CartDeleteView.as_view()(request, pk=cart.pk)
    cart.refresh_from_db()
    assert response.status_code == 200
    assert cart.deleted, "cart deleted successfully"


@pytest.mark.django_db
def test_cart_add_all(rf, regular_user):
    cart = _save_cart_with_products(rf, regular_user)
    request = apply_request_middleware(rf.post("/"), customer=get_person_contact(regular_user), user=regular_user)
    assert not request.basket.product_count, "cart is empty"
    response = CartAddAllProductsView.as_view()(request, pk=cart.pk)
    assert response.status_code == 200
    assert request.basket.product_count, "products added to cart"


@pytest.mark.django_db
def test_cart_add_all_with_errors(rf, regular_user):
    cart = _save_cart_with_products(rf, regular_user)
    for product in cart.products.all():
        product.deleted = True
        product.save()
    request = apply_request_middleware(rf.post("/"), customer=get_person_contact(regular_user), user=regular_user)
    assert not request.basket.product_count, "cart is empty"
    response = CartAddAllProductsView.as_view()(request, pk=cart.pk)
    data = json.loads(response.content.decode("utf8"))

    assert response.status_code == 200
    assert not request.basket.product_count, "no products added to cart"
    assert len(data["errors"]) > 0
