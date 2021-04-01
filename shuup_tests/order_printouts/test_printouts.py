# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.apps.provides import override_provides
from shuup.order_printouts.admin_module.views import get_confirmation_pdf, get_delivery_html, get_delivery_pdf
from shuup.order_printouts.utils import PrintoutDeliveryExtraInformation
from shuup.testing.factories import (
    create_order_with_product,
    create_product,
    get_default_shop,
    get_default_staff_user,
    get_default_supplier,
    get_shop,
)
from shuup.testing.utils import apply_request_middleware
from shuup.utils.excs import Problem
from shuup.utils.importing import load


class PrintoutTestDeliveryExtraFields(PrintoutDeliveryExtraInformation):
    @property
    def extra_fields(self):
        return {"Phone": "123456789", "Random": "row"}


@pytest.mark.django_db
def test_printouts(rf):
    try:
        import weasyprint
    except ImportError:
        pytest.skip()

    shop = get_default_shop()
    supplier = get_default_supplier()

    def test_delivery_and_confirmation_pdf(shop, supplier):
        product = create_product("simple-test-product-%s-" % shop.pk, shop)
        order = create_order_with_product(product, supplier, 6, 6, shop=shop)
        shipment = order.create_shipment_of_all_products(supplier)
        request = apply_request_middleware(rf.get("/"), user=get_default_staff_user())
        response = get_delivery_pdf(request, shipment.id)
        assert response.status_code == 200
        response = get_confirmation_pdf(request, order.id)
        assert response.status_code == 200

    test_delivery_and_confirmation_pdf(shop, supplier)  # Should be fine for first shop
    with pytest.raises(Problem):  # Second shop should fail since request shop does not match
        new_shop = get_shop(True, "USD", enabled=True)
        supplier.shops.add(new_shop)
        test_delivery_and_confirmation_pdf(new_shop, supplier)


@pytest.mark.django_db
def test_printouts_no_addresses(rf):
    try:
        import weasyprint
    except ImportError:
        pytest.skip()

    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    order = create_order_with_product(product, supplier, 6, 6, shop=shop)

    order.billing_address = None
    order.save()
    shipment = order.create_shipment_of_all_products(supplier)
    request = apply_request_middleware(rf.get("/"), user=get_default_staff_user())
    response = get_delivery_pdf(request, shipment.id)
    assert response.status_code == 200
    response = get_confirmation_pdf(request, order.id)
    assert response.status_code == 200

    order.shipping_address = None
    order.save()
    response = get_delivery_pdf(request, shipment.id)
    assert response.status_code == 200
    response = get_confirmation_pdf(request, order.id)
    assert response.status_code == 200


@pytest.mark.django_db
def test_adding_extra_fields_to_the_delivery(rf):
    try:
        import weasyprint
    except ImportError:
        pytest.skip()

    shop = get_default_shop()
    supplier = get_default_supplier()
    product = create_product("simple-test-product", shop)
    order = create_order_with_product(product, supplier, 6, 6, shop=shop)
    shipment = order.create_shipment_of_all_products(supplier)
    request = apply_request_middleware(rf.get("/"), user=get_default_staff_user())

    with override_provides(
        "order_printouts_delivery_extra_fields",
        [
            "shuup_tests.order_printouts.test_printouts:PrintoutTestDeliveryExtraFields",
        ],
    ):
        response = get_delivery_html(request, shipment.id)
        assert response.status_code == 200
        assert "123456789" in response.content.decode()
        assert "Random" in response.content.decode()
