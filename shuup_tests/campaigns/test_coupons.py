# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text

from shuup.campaigns.models.campaigns import BasketCampaign, Coupon
from shuup.testing import factories


@pytest.mark.django_db
def test_utf8_coupon_force_text(rf):
    code = u"HEINÄ"
    coupon = Coupon(code=code)
    try:
        text = force_text(coupon)
    except UnicodeDecodeError:
        text = ""
    assert text == code


@pytest.mark.django_db
def test_same_codes():
    shop1 = factories.get_shop(True, "EUR")
    shop2 = factories.get_shop(True, "USD")

    dc1 = Coupon.objects.create(code="TEST")
    dc2 = Coupon.objects.create(code="TEST")

    BasketCampaign.objects.create(name="test1", active=True, shop_id=shop1.id, coupon_id=dc1.id)
    with pytest.raises(ValidationError):
        BasketCampaign.objects.create(name="test1", active=True, shop_id=shop1.id, coupon_id=dc2.id)

    BasketCampaign.objects.create(name="test2", active=True, shop_id=shop2.id, coupon_id=dc2.id)
    with pytest.raises(ValidationError):
        BasketCampaign.objects.create(name="test2", active=True, shop_id=shop2.id, coupon_id=dc1.id)

    # Disable one campaigns for dc1 and you should be able to set the code to different campaign again
    dc3 = Coupon.objects.create(code="TEST")
    BasketCampaign.objects.filter(coupon=dc1).update(active=False)
    BasketCampaign.objects.create(name="test1", active=True, shop_id=shop1.id, coupon_id=dc3.id)

    # Try to reactivate the campaign for shop1
    c = BasketCampaign.objects.filter(coupon=dc1).first()
    assert c.active == False
    with pytest.raises(ValidationError):
        c.active = True
        c.save()

    # Try to sneak one duplicate code by saving the coupon
    dc4 = Coupon.objects.create(code="TEST1")
    BasketCampaign.objects.create(name="test4", active=True, shop_id=shop2.id, coupon_id=dc4.id)
    with pytest.raises(ValidationError):
        dc4.code = "TEST"
        dc4.save()
