# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import decimal
import pytest
from django.conf import settings

from shuup.apps.provides import override_provides
from shuup.core.pricing import (
    DiscountModule,
    PriceInfo,
    get_price_info,
    get_price_infos,
    get_pricing_steps,
    get_pricing_steps_for_products,
)
from shuup.testing.factories import create_product, get_default_shop
from shuup.testing.utils import apply_request_middleware

provide_overrider = override_provides("discount_module", [__name__ + ":Minus25DiscountModule"])


def setup_module(module):
    global original_pricing_module
    global original_discount_modules

    original_pricing_module = settings.SHUUP_PRICING_MODULE
    original_discount_modules = settings.SHUUP_DISCOUNT_MODULES

    settings.SHUUP_PRICING_MODULE = "default_pricing"
    settings.SHUUP_DISCOUNT_MODULES = ["minus25"]
    provide_overrider.__enter__()


def teardown_module(module):
    global original_pricing_module
    global original_discount_modules

    provide_overrider.__exit__(None, None, None)
    settings.SHUUP_PRICING_MODULE = original_pricing_module
    settings.SHUUP_DISCOUNT_MODULES = original_discount_modules


class Minus25DiscountModule(DiscountModule):
    identifier = "minus25"

    def discount_price(self, context, product, price_info):
        return PriceInfo(
            price=price_info.price * (1 - decimal.Decimal("0.25")),
            base_price=price_info.base_price,
            quantity=price_info.quantity,
            expires_on=price_info.expires_on,
        )


def initialize_test(rf):
    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    apply_request_middleware(request)
    product1 = create_product("test-product1", shop=shop, default_price=120)
    product2 = create_product("test-product2", shop=shop, default_price=180)
    return (request, [product1, product2], shop.create_price)


@pytest.mark.django_db
def test_get_price_info(rf):
    (request, products, price) = initialize_test(rf)
    pi = get_price_info(request, products[0])
    assert pi.price == price(90)
    assert pi.base_price == price(120)
    assert pi.quantity == 1


@pytest.mark.django_db
def test_get_price_info_with_quantity(rf):
    (request, products, price) = initialize_test(rf)
    pi = get_price_info(request, products[0], 20)
    assert pi.price == price(1800)
    assert pi.base_price == price(2400)
    assert pi.quantity == 20


@pytest.mark.django_db
def test_product_get_price_info(rf):
    (request, products, price) = initialize_test(rf)
    pi = products[0].get_price_info(request)
    assert pi.price == price(90)
    assert pi.base_price == price(120)


@pytest.mark.django_db
def test_get_price_infos(rf):
    (request, products, price) = initialize_test(rf)
    pis = get_price_infos(request, products)
    assert set(pis.keys()) == set(x.id for x in products)
    pi1 = pis[products[0].id]
    pi2 = pis[products[1].id]
    assert pi1.price == price(90)
    assert pi1.base_price == price(120)
    assert pi2.price == price(135)
    assert pi2.base_price == price(180)


@pytest.mark.django_db
def test_get_pricing_steps(rf):
    (request, products, price) = initialize_test(rf)
    pis = get_pricing_steps(request, products[0])
    assert len(pis) == 1
    assert pis[0].quantity == 1
    assert pis[0].price == price(90)
    assert pis[0].base_price == price(120)


@pytest.mark.django_db
def test_get_pricing_steps_for_products(rf):
    (request, products, price) = initialize_test(rf)
    pis = get_pricing_steps_for_products(request, products)
    assert set(pis.keys()) == set(x.id for x in products)
    assert len(pis[products[0].id]) == 1
    assert len(pis[products[1].id]) == 1
    assert pis[products[0].id][0].quantity == 1
    assert pis[products[0].id][0].price == price(90)
    assert pis[products[0].id][0].base_price == price(120)
    assert pis[products[1].id][0].quantity == 1
    assert pis[products[1].id][0].price == price(135)
    assert pis[products[1].id][0].base_price == price(180)
