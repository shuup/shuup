# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

import json
import pytest
from babel.dates import format_date
from django.utils.encoding import force_text

from shuup.campaigns.models.basket_effects import BasketDiscountAmount
from shuup.campaigns.models.campaigns import BasketCampaign, Coupon
from shuup.campaigns.reports import CouponsUsageReport
from shuup.core.models import Order
from shuup.core.order_creator import OrderCreator
from shuup.reports.forms import DateRangeChoices
from shuup.reports.writer import get_writer_instance
from shuup.testing.factories import (
    OrderLineType,
    create_random_person,
    get_address,
    get_default_payment_method,
    get_default_product,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_default_tax_class,
    get_initial_order_status,
)
from shuup.utils.i18n import get_current_babel_locale
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


def get_default_campaign(coupon, discount="20"):
    shop = get_default_shop()
    campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", coupon=coupon, active=True)
    BasketDiscountAmount.objects.create(discount_amount=shop.create_price(discount), campaign=campaign)
    return campaign


def seed_source(coupon, produce_price=10):
    source = BasketishOrderSource(get_default_shop())
    billing_address = get_address()
    shipping_address = get_address(name="Shippy Doge")
    source.status = get_initial_order_status()
    source.billing_address = billing_address
    source.shipping_address = shipping_address
    source.customer = create_random_person()
    source.payment_method = get_default_payment_method()
    source.shipping_method = get_default_shipping_method()
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=get_default_product(),
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(produce_price),
    )
    source.add_code(coupon.code)
    return source


@pytest.mark.django_db
def test_coupons_usage_report(rf):
    shop = get_default_shop()
    get_default_tax_class()
    creator = OrderCreator()

    coupon1 = Coupon.objects.create(code="coupon1", active=True)
    coupon2 = Coupon.objects.create(code="coupon2", active=True)

    get_default_campaign(coupon1, "10")
    get_default_campaign(coupon2, "25")

    source1 = seed_source(coupon1)
    source2 = seed_source(coupon1)
    source3 = seed_source(coupon1)
    source4 = seed_source(coupon2)

    creator.create_order(source1)
    creator.create_order(source2)
    creator.create_order(source3)
    creator.create_order(source4)

    # pay orders
    [o.create_payment(o.taxful_total_price) for o in Order.objects.all()]

    data = {
        "report": CouponsUsageReport.get_name(),
        "shop": shop.pk,
        "date_range": DateRangeChoices.ALL_TIME,
        "writer": "json",
        "force_download": 1,
    }
    report = CouponsUsageReport(**data)
    writer = get_writer_instance(data["writer"])
    response = writer.get_response(report=report)
    if hasattr(response, "render"):
        response.render()
    json_data = json.loads(response.content.decode("utf-8"))
    assert force_text(CouponsUsageReport.title) in json_data.get("heading")
    data = json_data.get("tables")[0].get("data")
    assert len(data) == Order.objects.count()

    expected_data = []

    orders = Order.objects.all().order_by("order_date")
    for order in orders:
        discount = order.shop.create_price(0)
        for dt in order.lines.discounts():
            discount += dt.taxful_price

        expected_data.append(
            {
                "date": format_date(order.order_date, locale=get_current_babel_locale()),
                "coupon": order.codes[0],
                "order": str(order),
                "taxful_total": float(order.taxful_total_price.as_rounded().value),
                "taxful_subtotal": float((order.taxful_total_price - discount).as_rounded().value),
                "total_discount": float(discount.as_rounded().value),
            }
        )

    assert len(expected_data) == len(data)

    for ix, d in enumerate(data):
        for k, v in d.items():
            assert expected_data[ix][k] == v
