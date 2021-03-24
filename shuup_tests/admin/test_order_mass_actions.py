# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import json
import pytest

from shuup.admin.modules.orders.mass_actions import (
    CancelOrderAction,
    OrderConfirmationPdfAction,
    OrderDeliveryPdfAction,
)
from shuup.admin.modules.orders.views import OrderListView
from shuup.core.models import Order, OrderStatusRole
from shuup.testing.factories import (
    create_product,
    create_random_order,
    create_random_person,
    get_default_shop,
    get_default_supplier,
)
from shuup.testing.utils import apply_request_middleware
from shuup_tests.utils import printable_gibberish

try:
    import weasyprint
except ImportError:
    weasyprint = None


@pytest.mark.django_db
def test_mass_edit_orders(rf, admin_user):
    shop = get_default_shop()

    supplier = get_default_supplier()
    contact1 = create_random_person()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="501")

    order = create_random_order(customer=contact1, products=[product1, product2], completion_probability=0)

    assert order.status.role != OrderStatusRole.CANCELED
    payload = {"action": CancelOrderAction().identifier, "values": [order.pk]}
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    request._body = json.dumps(payload).encode("UTF-8")
    view = OrderListView.as_view()
    response = view(request=request)
    assert response.status_code == 200
    for order in Order.objects.all():
        assert order.status.role == OrderStatusRole.CANCELED


@pytest.mark.django_db
def test_mass_edit_orders2(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    contact1 = create_random_person()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="501")

    order = create_random_order(customer=contact1, products=[product1, product2], completion_probability=0)

    assert order.status.role != OrderStatusRole.CANCELED
    payload = {"action": OrderConfirmationPdfAction().identifier, "values": [order.pk]}
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    request._body = json.dumps(payload).encode("UTF-8")
    view = OrderListView.as_view()
    response = view(request=request)
    assert response.status_code == 200
    if weasyprint:
        assert response["Content-Disposition"] == "attachment; filename=order_%s_confirmation.pdf" % order.pk
    else:
        assert response["content-type"] == "application/json"


@pytest.mark.django_db
def test_mass_edit_orders3(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    contact1 = create_random_person()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="501")

    order1 = create_random_order(customer=contact1, products=[product1, product2], completion_probability=0)

    order2 = create_random_order(customer=contact1, products=[product1, product2], completion_probability=0)
    assert order1.status.role != OrderStatusRole.CANCELED
    assert order2.status.role != OrderStatusRole.CANCELED

    payload = {"action": OrderConfirmationPdfAction().identifier, "values": [order1.pk, order2.pk]}
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    request._body = json.dumps(payload).encode("UTF-8")
    view = OrderListView.as_view()
    response = view(request=request)
    assert response.status_code == 200
    if weasyprint:
        assert response["Content-Disposition"] == "attachment; filename=order_confirmation_pdf.zip"
    else:
        assert response["content-type"] == "application/json"


@pytest.mark.django_db
def test_mass_edit_orders4(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    contact1 = create_random_person()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="501")

    order = create_random_order(customer=contact1, products=[product1, product2], completion_probability=0)

    assert order.status.role != OrderStatusRole.CANCELED

    payload = {"action": OrderDeliveryPdfAction().identifier, "values": [order.pk]}
    request = apply_request_middleware(rf.post("/"), user=admin_user)
    request._body = json.dumps(payload).encode("UTF-8")
    view = OrderListView.as_view()
    response = view(request=request)
    assert response.status_code == 200
    assert response["content-type"] == "application/json"

    order.create_shipment_of_all_products(supplier)
    order.save()
    request._body = json.dumps(payload).encode("UTF-8")
    view = OrderListView.as_view()
    response = view(request=request)
    assert response.status_code == 200

    if weasyprint:
        assert response["Content-Disposition"] == "attachment; filename=shipment_%s_delivery.pdf" % order.pk
    else:
        assert response["content-type"] == "application/json"


@pytest.mark.django_db
def test_mass_edit_orders5(rf, admin_user):
    shop = get_default_shop()
    supplier = get_default_supplier()
    contact1 = create_random_person()
    product1 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="50")
    product2 = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price="501")

    order1 = create_random_order(customer=contact1, products=[product1, product2], completion_probability=0)

    order2 = create_random_order(customer=contact1, products=[product1, product2], completion_probability=0)
    assert order1.status.role != OrderStatusRole.CANCELED
    assert order2.status.role != OrderStatusRole.CANCELED

    payload = {"action": OrderDeliveryPdfAction().identifier, "values": [order1.pk, order2.pk]}
    request = apply_request_middleware(rf.post("/"), user=admin_user)

    order1.create_shipment_of_all_products(supplier)
    order1.save()
    order2.create_shipment_of_all_products(supplier)
    order2.save()

    request._body = json.dumps(payload).encode("UTF-8")
    view = OrderListView.as_view()
    response = view(request=request)
    assert response.status_code == 200
    if weasyprint:
        assert response["Content-Disposition"] == "attachment; filename=order_delivery_pdf.zip"
    else:
        assert response["content-type"] == "application/json"
