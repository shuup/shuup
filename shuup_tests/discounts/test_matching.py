# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import AnonymousContact, CompanyContact, PersonContact
from shuup.discounts.models import Discount
from shuup.testing import factories
from shuup.testing.utils import apply_request_middleware


def _init_test_for_product(rf, default_price):
    shop = factories.get_default_shop()
    supplier = factories.get_default_supplier()
    request = rf.get("/")
    request.shop = shop
    apply_request_middleware(request)
    assert request.shop == shop

    product = factories.create_product("test", shop=shop, supplier=supplier, default_price=default_price)
    assert product.get_price_info(request).price == shop.create_price(default_price)
    return request, product


@pytest.mark.django_db
def test_matching_product_discount(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    discount_amount = 4
    Discount.objects.create(shop=request.shop, active=True, product=product, discount_amount_value=discount_amount)
    assert product.get_price_info(request).price == request.shop.create_price(default_price - discount_amount)


@pytest.mark.django_db
def test_matching_product_discount_with_category(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    product_discount_amount = 4
    Discount.objects.create(
        shop=request.shop, active=True, product=product, discount_amount_value=product_discount_amount
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    another_product = factories.create_product("test1", shop=request.shop, default_price=default_price)
    category = factories.get_default_category()
    another_product.get_shop_instance(request.shop).categories.add(category)
    assert another_product.get_price_info(request).price == request.shop.create_price(default_price)

    # Let's create category with some discounts
    category_discount_amount = 8
    Discount.objects.create(
        shop=request.shop, active=True, category=category, discount_amount_value=category_discount_amount
    )
    assert another_product.get_price_info(request).price == (
        request.shop.create_price(default_price - category_discount_amount)
    )

    # Category discount is bigger than product discount
    # so let's set this category for the first product too
    product.get_shop_instance(request.shop).categories.add(category)
    assert product.get_price_info(request).price == request.shop.create_price(default_price - category_discount_amount)

    # Let's create worse discount for category and make sure we have
    # multiple lines matching for these products and the best discount
    # is activated.
    Discount.objects.create(
        shop=request.shop, active=True, category=category, discount_amount_value=category_discount_amount - 3
    )

    assert another_product.get_price_info(request).price == (
        request.shop.create_price(default_price - category_discount_amount)
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - category_discount_amount)


@pytest.mark.django_db
def test_matching_product_discount_with_contact(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    product_discount_amount = 4
    discount = Discount.objects.create(
        shop=request.shop, active=True, product=product, discount_amount_value=product_discount_amount
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Adding contact condition to the discount should make
    # the discount go away.
    random_contact = factories.create_random_person()
    discount.contact = random_contact
    discount.save()
    assert request.customer != random_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Let's set the new contact as request customer and we
    # should get the discount back.
    request.customer = random_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Another contact should still only get the price without discount
    another_contact = factories.create_random_person()
    request.customer = another_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price)


@pytest.mark.django_db
def test_matching_product_discount_with_contact_group(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    product_discount_amount = 4
    discount = Discount.objects.create(
        shop=request.shop, active=True, product=product, discount_amount_value=product_discount_amount
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Adding contact group limitation to the discount should
    # make the discount go away
    contact_group = factories.get_default_customer_group()
    discount.contact_group = contact_group
    discount.save()
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Let's set contact for request with the group created
    # and let's see the discount coming back.
    random_contact = factories.create_random_person()
    request.customer = random_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price)
    random_contact.groups.add(contact_group)
    assert request.customer == random_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)


@pytest.mark.django_db
def test_category_product_discount_with_contact(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    category = factories.get_default_category()
    category.shop_products.add(product.get_shop_instance(request.shop))
    product_discount_amount = 4
    discount = Discount.objects.create(
        shop=request.shop, active=True, category=category, discount_amount_value=product_discount_amount
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Adding contact condition to the discount should make
    # the discount go away.
    random_contact = factories.create_random_person()
    discount.contact = random_contact
    discount.save()
    assert request.customer != random_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Let's set the new contact as request customer and we
    # should get the discount back.
    request.customer = random_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Another contact should still only get the price without discount
    another_contact = factories.create_random_person()
    request.customer = another_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price)


@pytest.mark.django_db
def test_category_selection_excluded(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    category = factories.get_default_category()
    product_discount_amount = 4
    Discount.objects.create(
        shop=request.shop,
        active=True,
        exclude_selected_category=True,
        category=category,
        discount_amount_value=product_discount_amount,
    )
    # applies to all products, except the selected category
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Setting default category for product disables the discount
    product.get_shop_instance(request.shop).categories.add(category)
    assert product.get_price_info(request).price == request.shop.create_price(default_price)


@pytest.mark.django_db
def test_category_product_discount_with_contact_group(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    category = factories.get_default_category()
    product.get_shop_instance(request.shop).categories.add(category)
    product_discount_amount = 4
    discount = Discount.objects.create(
        shop=request.shop, active=True, category=category, discount_amount_value=product_discount_amount
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Adding contact group limitation to the discount should
    # make the discount go away
    contact_group = factories.get_default_customer_group()
    discount.contact_group = contact_group
    discount.save()
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Let's set contact for request with the group created
    # and let's see the discount coming back
    random_contact = factories.create_random_person()
    request.customer = random_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price)
    random_contact.groups.add(contact_group)
    assert request.customer == random_contact
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)


@pytest.mark.django_db
def test_contact_discount(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    # Just to demonstrate that discounts can be created without products
    # and categories. This contacts gets $2 off from every product.
    product_discount_amount = 2
    random_company = factories.create_random_company()
    request.customer = random_company

    Discount.objects.create(
        shop=request.shop, active=True, contact=random_company, discount_amount_value=product_discount_amount
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    new_product_price = 7
    new_product = factories.create_product("test1", shop=request.shop, default_price=new_product_price)
    assert new_product.get_price_info(request).price == (
        request.shop.create_price(new_product_price - product_discount_amount)
    )

    # Changing the request customer drops the $2 discount
    request.customer = factories.create_random_company()
    assert product.get_price_info(request).price == request.shop.create_price(default_price)
    assert new_product.get_price_info(request).price == request.shop.create_price(new_product_price)


@pytest.mark.django_db
def test_contact_group_discount(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)

    # Just to demonstrate that discounts can be created without products
    # and categories. This contact group gets $2 off from every product.
    product_discount_amount = 2
    random_company = factories.create_random_company()
    contact_group = factories.get_default_customer_group()
    random_company.groups.add(contact_group)
    request.customer = random_company

    Discount.objects.create(
        shop=request.shop, active=True, contact_group=contact_group, discount_amount_value=product_discount_amount
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    new_product_price = 7
    new_product = factories.create_product("test1", shop=request.shop, default_price=new_product_price)
    assert new_product.get_price_info(request).price == (
        request.shop.create_price(new_product_price - product_discount_amount)
    )

    # Changing the request customer drops the $2 discount
    request.customer = factories.create_random_company()
    assert not request.customer.groups.filter(id=contact_group.pk).exists()
    assert product.get_price_info(request).price == request.shop.create_price(default_price)
    assert new_product.get_price_info(request).price == request.shop.create_price(new_product_price)


@pytest.mark.django_db
def test_discount_for_anons(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)
    assert request.customer == AnonymousContact()

    anon_default_group = AnonymousContact().get_default_group()
    product_discount_amount = 2
    Discount.objects.create(
        shop=request.shop, active=True, contact_group=anon_default_group, discount_amount_value=product_discount_amount
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Setting customer to request takes out the discount
    request.customer = factories.create_random_person()
    assert product.get_price_info(request).price == request.shop.create_price(default_price)


@pytest.mark.django_db
def test_discount_for_person_contacts(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)
    assert request.customer == AnonymousContact()

    product_discount_amount = 2
    Discount.objects.create(
        shop=request.shop,
        active=True,
        contact_group=PersonContact.get_default_group(),
        discount_amount_value=product_discount_amount,
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Setting customer to request activates the discount
    request.customer = factories.create_random_person()
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Using company contact as customer means no discount
    request.customer = factories.create_random_company()
    assert product.get_price_info(request).price == request.shop.create_price(default_price)


@pytest.mark.django_db
def test_discount_for_companies(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)
    assert request.customer == AnonymousContact()

    product_discount_amount = 2
    Discount.objects.create(
        shop=request.shop,
        active=True,
        contact_group=CompanyContact.get_default_group(),
        discount_amount_value=product_discount_amount,
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # Setting customer to request activates the discount
    request.customer = factories.create_random_company()
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Using person contact as customer means no discount
    request.customer = factories.create_random_person()
    assert product.get_price_info(request).price == request.shop.create_price(default_price)


@pytest.mark.django_db
def test_discount_for_logged_in_contacts(rf):
    default_price = 10
    request, product = _init_test_for_product(rf, default_price)
    assert request.customer == AnonymousContact()

    product_discount_amount = 2
    Discount.objects.create(
        shop=request.shop,
        active=True,
        contact_group=PersonContact.get_default_group(),
        discount_amount_value=product_discount_amount,
    )
    Discount.objects.create(
        shop=request.shop,
        active=True,
        contact_group=CompanyContact.get_default_group(),
        discount_amount_value=product_discount_amount,
    )
    assert product.get_price_info(request).price == request.shop.create_price(default_price)

    # setting customer to request should apply the discount
    request.customer = factories.create_random_person()
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)

    # Company as customer should work too
    request.customer = factories.create_random_company()
    assert product.get_price_info(request).price == request.shop.create_price(default_price - product_discount_amount)
