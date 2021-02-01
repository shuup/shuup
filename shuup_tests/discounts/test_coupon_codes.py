# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.basket import get_basket
from shuup.core.models import AnonymousContact, Product
from shuup.core.order_creator import OrderCreator
from shuup.discounts.models import CouponCode, CouponUsage, Discount
from shuup.discounts.modules import CouponCodeModule
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware
from shuup.core.pricing import get_price_info


def _init_test_for_product_without_basket(rf, default_price):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    random_customer = factories.create_random_person()
    request = rf.get("/")
    apply_request_middleware(request, shop=shop, customer=random_customer)
    assert request.shop == shop
    assert request.customer == random_customer

    sku = "test"
    product = Product.objects.filter(sku=sku).first()
    if not product:
        product = factories.create_product(sku, shop=shop, supplier=supplier, default_price=default_price)

    assert product.get_price_info(request).price == shop.create_price(default_price)
    return request, product


def _init_test_for_product_with_basket(rf, default_price):
    request, product = _init_test_for_product_without_basket(rf, default_price)
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    basket = get_basket(request)
    basket.status = factories.get_initial_order_status()
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = factories.get_shipping_method(shop=shop)
    basket.payment_method = factories.get_payment_method(shop=shop)
    assert basket.shop == request.shop
    assert basket.customer == request.customer
    return request, product, basket


@pytest.mark.django_db
def test_matching_coupon_code(rf):
    default_price = 10
    request, product = _init_test_for_product_without_basket(rf, default_price)

    discount_amount = 4
    coupon_code = CouponCode.objects.create(code="HORSESHOW2018", active=True)
    coupon_code.shops.add(request.shop)
    discount = Discount.objects.create(
        active=True, product=product, coupon_code=coupon_code, discount_amount_value=discount_amount)
    discount.shops.add(request.shop)

    # No basket means no coupon code in basket which means no discount
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    request, product, basket = _init_test_for_product_with_basket(rf, default_price)
    assert request.basket == basket

    # Ok now we have basket, but the coupon is not yet applied
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Make sure disabling discount makes coupon un-usable
    coupon_code_modifier = CouponCodeModule()
    assert coupon_code_modifier.can_use_code(request.basket, coupon_code.code)

    discount.active = False
    discount.save()
    assert not coupon_code_modifier.can_use_code(request.basket, coupon_code.code)

    discount.active = True
    discount.save()
    assert coupon_code_modifier.can_use_code(request.basket, coupon_code.code)

    basket.add_code(coupon_code)
    assert coupon_code.code in basket.codes
    assert coupon_code.code in request.basket.codes

    get_price_info(context=request, product=product.id) # Test if get_price_info works with product.id sent
    assert product.get_price_info(request).price == request.shop.create_price(default_price - discount_amount)

    # Apply coupon code after order is created
    basket.clear_codes()
    creator = OrderCreator()
    order = creator.create_order(basket)
    assert order.taxful_total_price == request.shop.create_price(default_price)

    # Make sure non active discount can't be used
    discount.active = False
    discount.save()
    order_modifier = CouponCodeModule()
    assert not order_modifier.use_code(order, coupon_code.code)
    discount.active = True
    discount.save()
    assert isinstance(order_modifier.use_code(order, coupon_code.code), CouponUsage)


@pytest.mark.django_db
def test_customer_usage_limit_for_anons(rf):
    default_price = 10
    request, product, basket = _init_test_for_product_with_basket(rf, default_price)

    discounted_price = 4
    coupon = CouponCode.objects.create(code="sUpErAle 123", active=True, usage_limit_customer=1)
    coupon.shops.add(request.shop)
    discount = Discount.objects.create(
        active=True, product=product, coupon_code=coupon, discounted_price_value=discounted_price)
    discount.shops.add(request.shop)
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    basket.add_code(coupon)
    assert basket.customer.pk is not None
    assert product.get_price_info(request).price == request.shop.create_price(discounted_price)

    # For anonymous contacts the discount is not there
    basket.customer = AnonymousContact()
    request.customer = basket.customer
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Anonymous contacts should get the discount after the
    # customer limit is removed.
    coupon.usage_limit_customer = None
    coupon.save()
    assert product.get_price_info(request).price == request.shop.create_price(discounted_price)

    # Deleting shop product should return zero price.
    # The zero price for product without shop product is
    # decided in the pricing module.
    shop_product = product.get_shop_instance(request.shop)
    shop_product.delete()
    assert product.get_price_info(request).price == request.shop.create_price(0)


def _create_order(request, customer, coupon, product, expected_product_price):
    creator = OrderCreator(request)
    shop = request.shop
    request.basket = None
    request.customer = customer
    basket = get_basket(request)
    basket.status = factories.get_initial_order_status()
    basket.add_product(supplier=factories.get_default_supplier(), shop=shop, product=product, quantity=1)
    basket.shipping_method = factories.get_shipping_method(shop=shop)
    basket.payment_method = factories.get_payment_method(shop=shop)
    basket.add_code(coupon)
    assert basket.shop == request.shop
    assert basket.customer == request.customer
    assert product.get_price_info(request).price == expected_product_price
    creator.create_order(basket)


@pytest.mark.django_db
def test_customer_usage_limit(rf):
    default_price = 10
    request, product = _init_test_for_product_without_basket(rf, default_price)
    shop = request.shop
    customers = []
    for x in range(3):
        customers.append(factories.create_random_company(shop=shop))

    discount_percentage = 0.20
    coupon = CouponCode.objects.create(code="sUpErAle", active=True, usage_limit_customer=2)
    coupon.shops.add(request.shop)
    discount = Discount.objects.create(
        active=True, product=product, coupon_code=coupon, discount_percentage=discount_percentage)
    discount.shops.add(request.shop)

    # Order product twice for each customer
    for customer in customers:
        for y in range(2):
            _create_order(request, customer, coupon, product, request.shop.create_price(8))

    assert coupon.usages.count() == 6  # Each customer 2 orders

    # Any of the customers created shouldn't be allowed to
    # order more with this coupon code.
    for customer in customers:
        assert not CouponCode.is_usable(shop, coupon, customer)

    # New customer should still be able to order some
    new_customer = factories.create_random_person()
    assert CouponCode.is_usable(shop, coupon, new_customer)
    _create_order(request, new_customer, coupon, product, request.shop.create_price(8))

    assert coupon.usages.count() == 7

    # Set usage limit and the new customer shouldn't be able to use the code
    coupon.usage_limit = 7
    coupon.save()
    assert not CouponCode.is_usable(request.shop, coupon, new_customer)
    _create_order(request, new_customer, coupon, product, request.shop.create_price(default_price))
    assert coupon.usages.count() == 7

    # One of the customer got refund
    refunded_customer = customers[0]
    order = refunded_customer.customer_orders.first()
    coupon_code_modifier = CouponCodeModule()
    coupon_code_modifier.clear_codes(order)

    assert coupon.usages.count() == 6

    # New customer still doesn't  able to create coupon
    new_customer = factories.create_random_person()
    assert CouponCode.is_usable(shop, coupon, new_customer)
    _create_order(request, new_customer, coupon, product, request.shop.create_price(8))
    assert coupon.usages.count() == 7


@pytest.mark.django_db
def test_usage_limit(rf):
    default_price = 10
    request, product, basket = _init_test_for_product_with_basket(rf, default_price)

    discounted_price = 4
    coupon_code = "TEST!2"
    shop = request.shop
    coupon = CouponCode.objects.create(code=coupon_code, active=True)
    coupon.shops.add(shop)
    discount = Discount.objects.create(
        active=True, product=product, coupon_code=coupon, discounted_price_value=discounted_price)
    discount.shops.add(request.shop)

    # Can not use coupon code that does not exist
    assert not CouponCode.is_usable(shop, "SIMO", basket.customer)

    # The coupon code should be usable
    assert CouponCode.is_usable(shop, coupon_code, basket.customer)
    assert coupon.can_use_code(shop, basket.customer)

    # Can not add coupon code that is not active
    coupon.active = False
    coupon.save()
    assert not CouponCode.is_usable(shop, coupon_code, basket.customer)
    assert not coupon.can_use_code(shop, basket.customer)

    # Re-activate coupon code
    coupon.active = True
    coupon.save()
    assert CouponCode.is_usable(shop, coupon_code, basket.customer)
    assert coupon.can_use_code(shop, basket.customer)

    # Can not use coupon code that is not attached
    discount.coupon_code = None
    discount.save()
    assert not CouponCode.is_usable(shop, coupon_code, basket.customer)

    # Re-attach discount
    discount.coupon_code = coupon
    discount.save()
    assert CouponCode.is_usable(shop, coupon_code, basket.customer)

    # Coupon code needs to be attached to current shop
    shop2 = factories.get_shop(prices_include_tax=True)
    assert not CouponCode.is_usable(shop2, coupon_code, basket.customer)
    assert CouponCode.is_usable(shop, coupon_code, basket.customer)

    coupon.shops.clear()
    assert not CouponCode.is_usable(shop, coupon_code, basket.customer)
    assert not coupon.can_use_code(shop, basket.customer)
    coupon.shops.add(shop)
    assert CouponCode.is_usable(shop, coupon_code, basket.customer)
    assert coupon.can_use_code(shop, basket.customer)

    # Coupon code not yet added to basket even if it is usable
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    basket.add_code(coupon)
    assert product.get_price_info(request).price == request.shop.create_price(discounted_price)

    order = factories.create_random_order()

    for x in range(50):
        coupon.use(order)

    assert coupon.usage_limit is None
    assert coupon.usages.count() == 50
    assert product.get_price_info(request).price == request.shop.create_price(discounted_price)

    # Set coupon usage limit 50
    coupon.usage_limit = 50
    coupon.save()

    assert not CouponCode.is_usable(shop, coupon.code, order.customer)
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Increase limit by 5
    coupon.usage_limit = 55
    coupon.save()

    for x in range(5):
        assert product.get_price_info(request).price == request.shop.create_price(discounted_price)
        coupon.use(order)

    assert coupon.usages.count() == 55
    assert not CouponCode.is_usable(shop, coupon.code, order.customer)
    assert product.get_price_info(request).price == request.shop.create_price(default_price)


@pytest.mark.django_db
def test_coupon_code_generation(rf):
    original_code = "random"
    coupon = CouponCode.objects.create(code=original_code, active=True)
    coupon.code = CouponCode.generate_code()
    coupon.save()
    assert coupon.code != original_code

    coupon.code = CouponCode.generate_code(length=62)
    coupon.save()
    assert coupon.code != original_code
    assert len(coupon.code) == 12
