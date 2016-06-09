# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.order_printouts.admin_module.views import get_confirmation_pdf, get_delivery_pdf
from shuup.testing.factories import (
    create_order_with_product, create_product, get_default_shop, get_default_supplier
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.importing import load


@pytest.mark.django_db
def test_printouts(rf):
    try:
        import weasyprint
    except ImportError:
        pytest.skip()

    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    order = create_order_with_product(product, supplier, 6, 6, shop=shop)
    shipment = order.create_shipment_of_all_products(supplier)
    request = rf.get("/")
    response = get_delivery_pdf(request, shipment.id)
    assert response.status_code == 200
    response = get_confirmation_pdf(request, order.id)
    assert response.status_code == 200


@pytest.mark.django_db
def test_toolbar_button(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    order = create_order_with_product(product, supplier, 6, 6, shop=shop)
    view = load("shuup.admin.modules.orders.views.OrderDetailView").as_view()
    request = apply_request_middleware(rf.get("/"), user=admin_user)
    response = view(request, pk=order.pk)
    expected_button_class = "SimplePrintoutsToolbarButton"
    toolbar = response.context_data.get("toolbar")
    assert any(button.__class__.__name__ == expected_button_class for button in toolbar)
    assert response.status_code == 200
