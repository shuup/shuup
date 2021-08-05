# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.conf import settings

from shuup.core.models import AnonymousContact, ContactGroup
from shuup.core.pricing import get_pricing_module
from shuup.core.utils.price_cache import cache_price_info, get_cached_price_info
from shuup.customer_group_pricing.models import CgpDiscount, CgpPrice
from shuup.customer_group_pricing.module import CustomerGroupPricingModule
from shuup.testing.factories import create_product, create_random_person, get_shop
from shuup.testing.utils import apply_request_middleware

pytestmark = pytest.mark.skipif(
    "shuup.customer_group_pricing" not in settings.INSTALLED_APPS, reason="customer_group_pricing not installed"
)

original_pricing_module = settings.SHUUP_PRICING_MODULE


def setup_module(module):
    settings.SHUUP_PRICING_MODULE = "customer_group_pricing"


def teardown_module(module):
    settings.SHUUP_PRICING_MODULE = original_pricing_module


def create_customer():
    customer = create_random_person()
    customer.groups.add(customer.get_default_group())
    customer.save()
    return customer


def initialize_test(rf, include_tax=False, customer=create_customer):
    domain = "shop-domain"
    shop = get_shop(prices_include_tax=include_tax, domain=domain)

    if callable(customer):
        customer = customer()

    request = apply_request_middleware(rf.get("/"), shop=shop, customer=customer, META={"HTTP_HOST": "%s" % domain})
    assert request.shop == shop
    assert request.customer == customer
    assert request.basket.shop == shop
    return request, shop, customer.groups.first()


def test_module_is_active():
    """
    Check that CustomerGroupPricingModule is active.
    """
    module = get_pricing_module()
    assert isinstance(module, CustomerGroupPricingModule)


@pytest.mark.django_db
def test_shop_specific_cheapest_price_1(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    product = create_product("Just-A-Product", shop, default_price=200)

    # CgpPrice.objects.create(product=product, shop=None, price=200)
    CgpPrice.objects.create(product=product, shop=shop, group=group, price_value=250)

    # Cheaper price is valid even if shop-specific price exists
    assert product.get_price(request, quantity=1) == price(200)


@pytest.mark.django_db
def test_shop_specific_cheapest_price_2(rf):
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=199)

    CgpPrice.objects.create(product=product, shop=shop, group=group, price_value=250)

    # Cheaper price is valid even if the other way around applies
    assert product.get_price(request, quantity=1) == price(199)


@pytest.mark.django_db
def test_set_taxful_price_works(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product = create_product("Anuva-Product", shop, default_price=300)

    # create ssp with higher price
    spp = CgpPrice(product=product, shop=shop, group=group, price_value=250)
    spp.save()

    price_info = product.get_price_info(request, quantity=1)

    assert price_info.price == price(250)
    assert product.get_price(request, quantity=1) == price(250)


@pytest.mark.django_db
def test_price_works_no_shop_product(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product = create_product("Anuva-Product", shop, default_price=300)

    # create ssp with higher price
    spp = CgpPrice(product=product, shop=shop, group=group, price_value=250)
    spp.save()
    price_info = product.get_price_info(request, quantity=1)
    assert price_info.price == price(250)
    assert product.get_price(request, quantity=1) == price(250)

    product.get_shop_instance(shop).delete()
    price_info = product.get_price_info(request, quantity=1)
    assert price_info.price == price(0)
    assert product.get_price(request, quantity=1) == price(0)


@pytest.mark.django_db
def test_set_taxful_price_works_with_product_id(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product = create_product("Anuva-Product", shop, default_price=300)

    # create ssp with higher price
    spp = CgpPrice(product=product, shop=shop, group=group, price_value=250)
    spp.save()

    price_info = product.get_price_info(request, quantity=1)

    assert price_info.price == price(250)

    assert product.get_price(request, quantity=1) == price(250)


@pytest.mark.django_db
def test_price_infos(rf, reindex_catalog):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product_one = create_product("Product_1", shop, default_price=150)
    product_two = create_product("Product_2", shop, default_price=250)

    spp = CgpPrice(product=product_one, shop=shop, group=group, price_value=100)
    spp.save()

    spp = CgpPrice(product=product_two, shop=shop, group=group, price_value=200)
    spp.save()
    reindex_catalog()

    product_ids = [product_one.pk, product_two.pk]

    spm = get_pricing_module()
    assert isinstance(spm, CustomerGroupPricingModule)
    pricing_context = spm.get_context_from_request(request)
    price_infos = spm.get_price_infos(pricing_context, product_ids)

    assert len(price_infos) == 2
    assert product_one.pk in price_infos
    assert product_two.pk in price_infos

    assert price_infos[product_one.pk].price == price(100)
    assert price_infos[product_two.pk].price == price(200)

    assert price_infos[product_one.pk].base_price == price(150)
    assert price_infos[product_two.pk].base_price == price(250)


@pytest.mark.django_db
def test_customer_is_anonymous(rf):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    product = create_product("random-1", shop=shop, default_price=100)

    CgpPrice.objects.create(product=product, group=group, shop=shop, price_value=50)

    request.customer = AnonymousContact()

    price_info = product.get_price_info(request)

    assert price_info.price == price(100)


@pytest.mark.django_db
def test_anonymous_customers_default_group(rf):
    request, shop, group = initialize_test(rf, True)
    discount_value = 49
    product = create_product("random-52", shop=shop, default_price=121)
    request.customer = AnonymousContact()
    CgpPrice.objects.create(
        product=product, group=request.customer.get_default_group(), shop=shop, price_value=discount_value
    )
    price_info = product.get_price_info(request)
    assert price_info.price == shop.create_price(discount_value)


@pytest.mark.django_db
def test_zero_default_price(rf, admin_user):
    request, shop, group = initialize_test(rf, True)
    price = shop.create_price

    # create a product with zero price
    product = create_product("random-1", shop=shop, default_price=0)

    CgpPrice.objects.create(product=product, group=group, shop=shop, price_value=50)

    price_info = product.get_price_info(request)

    assert price_info.price == price(50)


@pytest.mark.parametrize("price,discount", [(10, 8), (8, 4), (4, 8), (999, 999)])
@pytest.mark.django_db
def test_discount_for_customer(rf, admin_user, price, discount):
    request, shop, group = initialize_test(rf, True)

    product = create_product("product", shop=shop, default_price=price)
    CgpDiscount.objects.create(product=product, group=group, shop=shop, discount_amount_value=discount)
    price_info = product.get_price_info(request)
    assert price_info.price == shop.create_price(max(price - discount, 0))


@pytest.mark.parametrize("price,discount", [(10, 8), (8, 4), (4, 8), (999, 999)])
@pytest.mark.django_db
def test_discount_for_anonymous(rf, admin_user, price, discount):
    request, shop, group = initialize_test(rf, True, AnonymousContact())

    product = create_product("product", shop=shop, default_price=price)
    CgpDiscount.objects.create(product=product, group=group, shop=shop, discount_amount_value=discount)
    price_info = product.get_price_info(request)
    assert price_info.price == shop.create_price(max(price - discount, 0))


@pytest.mark.parametrize("price, discount, anonymous_discount", [(10, 8, 6), (8, 4, 3), (4, 8, 8), (999, 999, 999)])
@pytest.mark.django_db
def test_discount_for_multi_group_using_customer(rf, admin_user, price, discount, anonymous_discount):
    customer = create_customer()
    anonymous = AnonymousContact()

    request, shop, _ = initialize_test(rf, True, customer)

    product = create_product("product", shop=shop, default_price=price)

    CgpDiscount.objects.create(
        product=product, group=customer.groups.first(), shop=shop, discount_amount_value=discount
    )
    CgpDiscount.objects.create(
        product=product, group=anonymous.get_default_group(), shop=shop, discount_amount_value=anonymous_discount
    )

    # discount for customer
    request, shop, _ = initialize_test(rf, True, customer)
    price_info = product.get_price_info(request)
    assert price_info.price == shop.create_price(max(price - discount, 0))

    # discount for anonymous
    request, shop, _ = initialize_test(rf, True, anonymous)
    price_info = product.get_price_info(request)
    assert price_info.price == shop.create_price(max(price - anonymous_discount, 0))


@pytest.mark.parametrize("price,discount,quantity", [(10, 8, 2), (8, 4, 3), (999, 999, 4)])
@pytest.mark.django_db
def test_discount_quantities(rf, admin_user, price, discount, quantity):
    request, shop, group = initialize_test(rf, True)

    product = create_product("product", shop=shop, default_price=price)
    CgpDiscount.objects.create(product=product, group=group, shop=shop, discount_amount_value=discount)

    price_info = product.get_price_info(request, quantity=quantity)
    discount_amount = discount * quantity

    assert price_info.price == shop.create_price((price * quantity) - discount_amount)
    assert price_info.base_unit_price == shop.create_price(price)
    assert price_info.discount_amount == shop.create_price(discount * quantity)


@pytest.mark.django_db
def test_price_info_cache_bump(rf):
    request, shop, group = initialize_test(rf, True)

    product_one = create_product("Product_1", shop, default_price=150)
    product_two = create_product("Product_2", shop, default_price=250)

    contact = create_customer()
    group2 = ContactGroup.objects.create(name="Group 2", shop=shop)

    cgp_price = CgpPrice.objects.create(product=product_one, shop=shop, group=group, price_value=100)
    cgp_discount = CgpDiscount.objects.create(product=product_two, shop=shop, group=group, discount_amount_value=200)

    spm = get_pricing_module()
    assert isinstance(spm, CustomerGroupPricingModule)
    pricing_context = spm.get_context_from_request(request)

    for function in [
        lambda: cgp_price.save(),
        lambda: cgp_discount.save(),
        lambda: group2.members.add(contact),
        lambda: cgp_price.delete(),
        lambda: cgp_discount.delete(),
    ]:
        cache_price_info(pricing_context, product_one, 1, product_one.get_price_info(pricing_context))
        cache_price_info(pricing_context, product_two, 1, product_two.get_price_info(pricing_context))

        # prices are cached
        assert get_cached_price_info(pricing_context, product_one)
        assert get_cached_price_info(pricing_context, product_two)

        # caches should be bumped
        function()
        assert get_cached_price_info(pricing_context, product_one) is None
        assert get_cached_price_info(pricing_context, product_two) is None
