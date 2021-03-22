# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from django.test import override_settings

from shuup.core.models import MutableAddress, OrderLineType, get_person_contact
from shuup.core.order_creator import OrderCreator
from shuup.testing.factories import (
    get_default_payment_method,
    get_default_product,
    get_default_shipping_method,
    get_default_shop,
    get_default_supplier,
    get_initial_order_status,
)
from shuup_tests.utils.basketish_order_source import BasketishOrderSource


def get_order_and_source(admin_user, product, language, language_fallback):
    # create original source to tamper with

    contact = get_person_contact(admin_user)
    contact.language = language
    contact.save()

    assert contact.language == language  # contact language is naive

    source = BasketishOrderSource(get_default_shop())
    source.status = get_initial_order_status()
    source.billing_address = MutableAddress.objects.create(name="Original Billing")
    source.shipping_address = MutableAddress.objects.create(name="Original Shipping")
    source.customer = contact
    source.payment_method = get_default_payment_method()
    source.shipping_method = get_default_shipping_method()
    source.add_line(
        type=OrderLineType.PRODUCT,
        product=product,
        supplier=get_default_supplier(),
        quantity=1,
        base_unit_price=source.create_price(10),
    )
    source.add_line(
        type=OrderLineType.OTHER,
        quantity=1,
        base_unit_price=source.create_price(10),
        require_verification=True,
    )
    assert len(source.get_lines()) == 2
    source.creator = admin_user

    assert not source._language  # is None because it was not directly assigned
    assert source.language == language_fallback

    creator = OrderCreator()
    order = creator.create_order(source)

    assert order.language == source.language

    return order, source


@pytest.mark.django_db
@pytest.mark.parametrize("lang_code", ["en", "fi", "sv", "ja", "zh-hans", "pt-br", "it"])
def test_order_language_fallbacks(rf, admin_user, lang_code):
    product = get_default_product()

    with override_settings(LANGUAGE_CODE=lang_code):
        languages = {
            0: ("en", "en"),  # English
            1: ("fi", "fi"),  # Finnish
            2: ("bew", lang_code),  # Betawi
            3: ("bss", lang_code),  # Akoose
            4: ("en_US", lang_code),  # American English
            5: ("is", "is"),  # Icelandic
            6: ("es_419", lang_code),  # Latin American Spanish
            7: ("nds_NL", lang_code),  # Low Saxon
            8: ("arn", lang_code),  # Mapuche
            9: ("sv", "sv"),  # swedish
        }
        for x in range(10):
            language = languages[x][0]
            fallback = languages[x][1]
            get_order_and_source(admin_user=admin_user, product=product, language=language, language_fallback=fallback)
