# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from bs4 import BeautifulSoup
from django.utils.translation import activate

from shuup.core.models import get_person_contact
from shuup.front.basket import get_basket
from shuup.front.checkout.methods import MethodsPhase
from shuup.front.views.checkout import BaseCheckoutView
from shuup.testing.factories import (
    create_product,
    get_default_shop,
    get_default_supplier,
    get_payment_method,
    get_shipping_method,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish

SHIPPING_DATA = {
    "name": "Home delivery",
    "description": "Delivery takes 3 years, sorry.",
}

PAYMENT_DATA = {
    "name": "Cash",
    "description": "No coins!",
}


class MethodsOnlyCheckoutView(BaseCheckoutView):
    phase_specs = ["shuup.front.checkout.methods:MethodsPhase"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "get_method,data,method_id,",
    [
        (get_shipping_method, SHIPPING_DATA, "id_shipping_method"),
        (get_payment_method, PAYMENT_DATA, "id_payment_method"),
    ],
)
def test_method_phase_basic(rf, admin_user, get_method, data, method_id):
    activate("en")
    shop = get_default_shop()
    method = get_method(shop, price=0, name=data["name"])
    method.description = data["description"]
    method.save()
    assert method.enabled

    view = MethodsOnlyCheckoutView.as_view()

    # To make method visible, basket must be available
    person = get_person_contact(admin_user)
    request = apply_request_middleware(rf.get("/"))
    request.shop = shop
    request.user = admin_user
    request.person = person
    request.customer = person
    basket = get_basket(request)

    # add product to bakset
    supplier = get_default_supplier()
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=50)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=2)
    assert basket.product_count, "basket has products"

    basket.save()
    request = apply_request_middleware(request, user=admin_user, person=person, customer=person, basket=basket)

    # request = apply_request_middleware(rf.get("/"))
    response = view(request=request, phase="methods")
    if hasattr(response, "render"):
        response.render()
    assert response.status_code in [200, 302]
    soup = BeautifulSoup(response.content)
    method_soup = soup.find("div", {"id": method_id})

    assert data["name"] in method_soup.text
    assert data["description"] in method_soup.text
    assert soup.find("input", {"id": "%s_%s" % (method_id, method.pk)})
