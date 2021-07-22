# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.http.response import Http404

from shuup.admin.modules.orders.views import (
    NewLogEntryView,
    OrderAddressEditView,
    OrderCreateFullRefundView,
    OrderCreatePaymentView,
    OrderCreateRefundView,
    OrderCreateShipmentView,
    OrderDeletePaymentView,
    OrderDetailView,
    OrderSetPaidView,
    OrderSetStatusView,
    ShipmentDeleteView,
    UpdateAdminCommentView,
)
from shuup.core.models import (
    Order,
    OrderLogEntry,
    OrderStatus,
    OrderStatusHistory,
    OrderStatusManager,
    OrderStatusRole,
    ShippingStatus,
)
from shuup.testing.factories import (
    create_order_with_product,
    create_product,
    create_random_order,
    create_random_person,
    create_random_user,
    get_default_product,
    get_default_shop,
    get_default_supplier,
    get_shop,
)
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_order_set_status_completed_works(admin_user, rf):
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    order.create_shipment_of_all_products()  # Need to be shipped to set complete
    assert order.status.role == OrderStatusRole.INITIAL
    complete_status = OrderStatus.objects.get_default_complete()
    view = OrderSetStatusView.as_view()
    request = apply_request_middleware(rf.post("/", {"status": complete_status.pk}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code < 400
    order = Order.objects.get(pk=order.pk)
    assert order.status_id == complete_status.id
    assert order.log_entries.filter(identifier="status_change").exists()


@pytest.mark.django_db
def test_order_set_status_canceled_works(admin_user, rf):
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    assert order.shipping_status == ShippingStatus.NOT_SHIPPED
    assert order.status.role == OrderStatusRole.INITIAL
    canceled_status = OrderStatus.objects.get_default_canceled()
    view = OrderSetStatusView.as_view()
    request = apply_request_middleware(rf.post("/", {"status": canceled_status.pk}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code < 400
    order = Order.objects.get(pk=order.pk)
    assert order.status_id == canceled_status.id
    assert order.log_entries.filter(identifier="status_change").exists()


@pytest.mark.django_db
def test_add_order_log_entry(admin_user, rf):
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    assert not OrderLogEntry.objects.filter(target=order).exists()
    view = NewLogEntryView.as_view()
    test_message = "test_order"
    request = apply_request_middleware(rf.post("/", {"message": test_message}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code < 400
    assert OrderLogEntry.objects.filter(target=order).exists()
    assert OrderLogEntry.objects.filter(target=order).first().message == test_message


@pytest.mark.django_db
def test_update_order_admin_comment(admin_user, rf):
    order = create_random_order(customer=create_random_person(), products=(get_default_product(),))
    assert order.admin_comment == ""
    view = UpdateAdminCommentView.as_view()
    comment = "updated admin comment"
    request = apply_request_middleware(rf.post("/", {"comment": comment}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code < 400
    order.refresh_from_db()
    assert order.admin_comment == comment


@pytest.mark.django_db
def test_delete_payment(admin_user, rf):
    product = get_default_product()
    shop_product = product.get_shop_instance(get_default_shop())
    shop_product.default_price_value = 20
    shop_product.save()

    order = create_random_order(customer=create_random_person(), products=(product,), completion_probability=0)
    payment_amount = order.taxful_total_price_value

    # create a payment
    view = OrderCreatePaymentView.as_view()
    request = apply_request_middleware(rf.post("/", {"amount": payment_amount}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code == 302

    order.refresh_from_db()
    assert order.is_paid()

    # delete the payment
    payment = order.payments.last()
    view = OrderDeletePaymentView.as_view()
    request = apply_request_middleware(rf.post("/", {"payment": payment.pk}), user=admin_user)
    response = view(request, pk=order.pk)
    assert response.status_code == 302

    order.refresh_from_db()
    assert order.is_not_paid()


@pytest.mark.django_db
def test_view_availability(admin_user, rf):
    supplier = get_default_supplier()
    shop_one = get_shop(True, "USD", enabled=True, identifier="one", name="Shop One")
    supplier.shops.add(shop_one)
    simone = create_random_user(username="simone")
    simone.is_staff = True
    simone.save()
    shop_one.staff_members.add(simone)

    peter = create_random_user(username="peter")
    peter.is_staff = True
    peter.save()
    shop_one.staff_members.add(peter)

    shop_two = get_shop(True, "USD", enabled=True, identifier="two", name="Shop Two")
    assert shop_one.pk != shop_two.pk
    supplier.shops.add(shop_two)
    calle = create_random_user(username="calle")
    calle.is_staff = True
    calle.save()
    shop_two.staff_members.add(calle)

    product = create_product("simple-test-product", shop_one)
    order = create_order_with_product(product, supplier, 6, 6, shop=shop_one)

    # Simone and Peter should access to this order. Calle should get 404
    def test_view(view, order, shop, user, data=None):
        if data:
            request = apply_request_middleware(rf.post("/", data), user=user, shop=shop)
        else:
            request = apply_request_middleware(rf.get("/"), user=user, shop=shop)

        response = view.as_view()(request, pk=order.pk)

    # Gets
    for view in [OrderDetailView, OrderSetStatusView, OrderCreatePaymentView, OrderSetPaidView, OrderAddressEditView]:
        test_view(view, order, shop_one, simone)
        test_view(view, order, shop_one, peter)
        with pytest.raises(Http404):
            test_view(view, order, shop_two, calle)

    test_view(NewLogEntryView, order, shop_one, simone, {"message": "message here"})
    test_view(NewLogEntryView, order, shop_one, peter, {"message": "message here"})
    with pytest.raises(Http404):
        test_view(NewLogEntryView, order, shop_two, calle, {"message": "message here"})

    test_view(UpdateAdminCommentView, order, shop_one, simone, {"comment": "comment here"})
    test_view(UpdateAdminCommentView, order, shop_one, peter, {"comment": "comment here"})
    with pytest.raises(Http404):
        test_view(UpdateAdminCommentView, order, shop_two, calle, {"comment": "comment here"})

    def test_shipment_view(order, shop, supplier, user):
        request = apply_request_middleware(rf.get("/"), user=user, shop=shop)
        response = OrderCreateShipmentView.as_view()(request, pk=order.pk, supplier_pk=supplier.pk)

    test_shipment_view(order, shop_one, supplier, simone)
    test_shipment_view(order, shop_one, supplier, peter)
    with pytest.raises(Http404):
        test_shipment_view(order, shop_two, supplier, calle)

    # Create shipment to test delete shipment view
    shipment = order.create_shipment_of_all_products(supplier)

    def test_shipment_delete_view(shipment, shop, user):
        request = apply_request_middleware(rf.post("/"), user=user, shop=shop)
        response = ShipmentDeleteView.as_view()(request, pk=shipment.pk, supplier_pk=supplier.pk)

    test_shipment_delete_view(shipment, shop_one, simone)
    test_shipment_delete_view(shipment, shop_one, peter)
    with pytest.raises(Http404):
        test_shipment_delete_view(shipment, shop_two, calle)

    # Create payment to test refund and delete payment view
    order.create_payment(order.taxful_total_price)
    payment = order.payments.first()
    assert payment is not None

    for view in [OrderCreateRefundView, OrderCreateFullRefundView]:
        test_view(view, order, shop_one, simone)
        test_view(view, order, shop_one, peter)
        with pytest.raises(Http404):
            test_view(view, order, shop_two, calle)

    def test_payment_delete_view(payment, shop, user):
        request = apply_request_middleware(rf.post("/"), user=user, shop=shop)
        response = OrderDeletePaymentView.as_view()(request, pk=payment.pk)

    test_payment_delete_view(payment, shop_one, simone)
    test_payment_delete_view(payment, shop_one, peter)
    with pytest.raises(Http404):
        test_payment_delete_view(payment, shop_two, calle)
