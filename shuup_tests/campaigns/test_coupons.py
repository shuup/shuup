# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from django.utils.encoding import force_text

from shuup.campaigns.models.campaigns import Coupon

@pytest.mark.django_db
def test_utf8_coupon_force_text(rf):
    code = u"HEINÄ"
    coupon = Coupon(code=code)
    try:
        text = force_text(coupon)
    except UnicodeDecodeError:
        text = ""
    assert text == code
