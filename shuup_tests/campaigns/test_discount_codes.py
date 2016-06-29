# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shuup Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.

"""
1) Check if the discount is only available with a discount code and type the code, or generate it with a click of a button
2) If discount code: How many available
3) If discount code: How many available for each user
"""
import pytest
from django.core.exceptions import ValidationError

from shuup.campaigns.models.basket_conditions import \
    BasketTotalProductAmountCondition
from shuup.campaigns.models.basket_effects import BasketDiscountAmount
from shuup.campaigns.models.campaigns import (
    BasketCampaign, Coupon, CouponUsage
)
from shuup.core.models import OrderLineType
from shuup.core.order_creator import OrderCreator
from shuup.front.basket import get_basket
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    get_default_shop, get_default_supplier, get_initial_order_status
)
from shuup_tests.campaigns import initialize_test
from shuup_tests.utils import printable_gibberish


def get_default_campaign(coupon=None):
    shop = get_default_shop()
    campaign = BasketCampaign.objects.create(
            shop=shop, public_name="test", name="test",
            coupon=coupon, active=True
    )
    BasketDiscountAmount.objects.create(discount_amount=shop.create_price("20"), campaign=campaign)
    return campaign

@pytest.mark.django_db
def test_coupon_generation():
    original_code = "random"
    coupon = Coupon.objects.create(code=original_code, active=True)
    coupon.code = Coupon.generate_code()
    coupon.save()
    assert coupon.code != original_code


@pytest.mark.django_db
def test_coupon_user_limit():
    coupon = Coupon.objects.create(code="TEST", active=True)
    get_default_campaign(coupon)
    contact = create_random_person()
    shop = get_default_shop()
    product = create_product("test", shop=shop, supplier=get_default_supplier(), default_price="12")
    order = create_random_order(customer=contact)
    for x in range(50):
       coupon.use(order)

    assert coupon.usages.count() == 50

    # set limit to coupon_usage
    coupon.increase_customer_usage_limit_by(5)
    coupon.save()

    assert coupon.usage_limit_customer == 55
    assert coupon.can_use_code(contact)
    for x in range(5):
        coupon.use(order)
    assert coupon.usages.count() == 55

    assert not Coupon.is_usable(coupon.code, order.customer)
    assert coupon.usages.count() == 55  # no change, limit met


@pytest.mark.django_db
def test_coupon_amount_limit():
    coupon = Coupon.objects.create(code="TEST", active=True)
    get_default_campaign(coupon)

    contact = create_random_person()
    shop = get_default_shop()
    product = create_product("test", shop=shop, supplier=get_default_supplier(), default_price="12")
    order = create_random_order(customer=contact)

    for x in range(50):
       coupon.use(order)

    assert coupon.usages.count() == 50
    coupon.increase_usage_limit_by(5)
    coupon.save()

    assert coupon.usage_limit == 55
    assert coupon.can_use_code(contact)

    for x in range(5):
        coupon.use(order)

    assert coupon.usages.count() == 55

    assert not Coupon.is_usable(coupon.code, order.customer)
    assert coupon.usages.count() == 55  # no change, limit met


@pytest.mark.django_db
def test_no_two_same_codes_active():
    # allow two discount codes with same code as they are inactive
    dc1 = Coupon.objects.create(code="TEST")
    dc2 = Coupon.objects.create(code="TEST")

    dc1.active = True
    dc1.save()

    dc2.active = True
    with pytest.raises(ValidationError):
        dc2.save()
    dc2.code = "changed_code"
    dc2.save()


@pytest.mark.django_db
def test_campaign_with_coupons(rf):
    status = get_initial_order_status()
    request, shop, group = initialize_test(rf, False)
    basket = get_basket(request)
    supplier = get_default_supplier()

    for x in range(2):
        product = create_product(printable_gibberish(), shop, supplier=supplier, default_price="50")
        basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)

    dc = Coupon.objects.create(code="TEST", active=True)
    campaign = BasketCampaign.objects.create(
            shop=shop,
            name="test", public_name="test",
            coupon=dc,
            active=True
    )
    BasketDiscountAmount.objects.create(discount_amount=shop.create_price("20"), campaign=campaign)
    rule = BasketTotalProductAmountCondition.objects.create(value=2)
    campaign.conditions.add(rule)
    campaign.save()

    assert len(basket.get_final_lines()) == 2  # no discount was applied because coupon is required

    basket.add_code(dc.code)

    assert len(basket.get_final_lines()) == 3  # now basket has codes so they will be applied too
    assert OrderLineType.DISCOUNT in [l.type for l in basket.get_final_lines()]

    # Ensure codes persist between requests, so do what the middleware would, i.e.
    basket.save()
    # and then reload the basket:
    del request.basket
    basket = get_basket(request)

    assert basket.codes == [dc.code]
    assert len(basket.get_final_lines()) == 3  # now basket has codes so they will be applied too
    assert OrderLineType.DISCOUNT in [l.type for l in basket.get_final_lines()]

    basket.status = status
    creator = OrderCreator(request)
    order = creator.create_order(basket)
    assert CouponUsage.objects.filter(order=order).count() == 1
    assert CouponUsage.objects.filter(order=order, coupon__code=dc.code).count() == 1
