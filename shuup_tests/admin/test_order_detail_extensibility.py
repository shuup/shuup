# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from bs4 import BeautifulSoup
from django.core.urlresolvers import reverse

from shuup.admin.modules.orders.views.detail import OrderDetailView
from shuup.apps.provides import override_provides
from shuup.testing.factories import create_empty_order, get_default_shop
from shuup.testing.utils import apply_request_middleware


@pytest.mark.django_db
def test_order_detail_has_default_toolbar_action_items(rf, admin_user):
    shop = get_default_shop()
    order = create_empty_order(shop=shop)
    order.save()

    request = apply_request_middleware(rf.get("/"), user=admin_user)
    view_func = OrderDetailView.as_view()
    create_payment_url = reverse("shuup_admin:order.create-payment", kwargs={"pk": order.pk})
    with override_provides("admin_order_toolbar_action_item", [
        "shuup.admin.modules.orders.toolbar:CreatePaymentAction"
    ]):
        assert _check_if_link_exists(view_func, request, order, create_payment_url)

    with override_provides("admin_order_toolbar_action_item", []):
        assert not _check_if_link_exists(view_func, request, order, create_payment_url)


def _check_if_link_exists(view_func, request, order, url):
    response = view_func(request, pk=order.pk)
    soup = BeautifulSoup(response.render().content)
    for dropdown_link in soup.find_all("a", {"class": "btn-default"}):
        if dropdown_link.get("href", "") == url:
            return True
    return False
