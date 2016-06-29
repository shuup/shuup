# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

import pytest

from bs4 import BeautifulSoup
from django.utils.translation import activate

from shuup.front.checkout.methods import MethodsPhase
from shuup.testing.factories import get_payment_method, get_shipping_method, get_default_shop
from shuup.testing.utils import apply_request_middleware

SHIPPING_DATA = {
    "name": "Home delivery",
    "description": "Delivery takes 3 years, sorry.",
}

PAYMENT_DATA = {
    "name": "Cash",
    "description": "No coins!",
}


@pytest.mark.django_db
@pytest.mark.parametrize("get_method,data,method_id,", [
    (get_shipping_method, SHIPPING_DATA, "id_shipping_method"),
    (get_payment_method, PAYMENT_DATA, "id_payment_method")
])
def test_method_phase_basic(rf, get_method, data, method_id):
    activate("en")
    shop = get_default_shop()
    method = get_method(shop, price=0, name=data["name"])
    method.description = data["description"]
    method.save()
    assert method.enabled

    view = MethodsPhase.as_view()
    request = apply_request_middleware(rf.get("/"))
    response = view(request=request)
    if hasattr(response, "render"):
        response.render()
    assert response.status_code in [200, 302]
    soup = BeautifulSoup(response.content)
    method_soup = soup.find("div", {"id": method_id})
    assert data["name"] in method_soup.text
    assert data["description"] in method_soup.text
    assert soup.find("input", {"id": "%s_%s" % (method_id, method.pk)})
