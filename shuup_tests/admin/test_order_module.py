# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shuup Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.admin.modules.orders.views import (
    NewLogEntryView, OrderCreatePaymentView, OrderDeletePaymentView,
    OrderSetStatusView, UpdateAdminCommentView
)
from shuup.core.models import (
    Order, OrderLogEntry, OrderStatus, OrderStatusRole, ShippingStatus
)
from shuup.testing.factories import (
    create_random_order, create_random_person, get_default_product,
    get_default_shop
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
