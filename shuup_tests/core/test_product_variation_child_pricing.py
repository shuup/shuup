# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest

from shuup.core.models import AnonymousContact, ContactGroup, ProductVisibility, get_person_contact
from shuup.testing.factories import create_product, get_default_product, get_default_shop, get_default_supplier
from shuup.testing.utils import apply_request_middleware


def init_test(request, shop, prices):
    apply_request_middleware(request)
    parent = create_product("parent_product", shop=shop)
    supplier = get_default_supplier(shop)
    children = [
        create_product("child-%d" % price, shop=shop, supplier=supplier, default_price=price) for price in prices
    ]
    for child in children:
        child.link_to_parent(parent)
    return parent


@pytest.mark.django_db
def test_simple_product_works(rf):
    product = get_default_product()
    request = rf.get("/")
    apply_request_middleware(request)
    assert product.get_child_price_range(request) == (None, None)
    assert product.get_cheapest_child_price_info(request) is None
    assert product.get_cheapest_child_price(request) is None


@pytest.mark.django_db
def test_cheapest_price_found(rf):
    prices = [100, 20, 50, 80, 90]

    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    parent = init_test(request, shop, prices)

    price = shop.create_price
    assert parent.get_cheapest_child_price(request) == price(min(prices))

    price_info = parent.get_cheapest_child_price_info(request)
    assert price_info.price == price(min(prices))


@pytest.mark.django_db
def test_correct_range_found(rf):
    prices = [100, 20, 50, 80, 90]

    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    parent = init_test(request, shop, prices)

    price = shop.create_price
    assert parent.get_child_price_range(request) == (price(min(prices)), price(max(prices)))


@pytest.mark.django_db
def test_only_one_variation_child(rf):
    prices = [20]

    shop = get_default_shop()
    request = rf.get("/")
    request.shop = shop
    parent = init_test(request, shop, prices)

    price_info = parent.get_cheapest_child_price_info(request)

    price = shop.create_price

    assert parent.get_cheapest_child_price(request) == price(min(prices))
    assert parent.get_child_price_range(request) == (price(min(prices)), price(max(prices)))
    assert price_info.price == price(min(prices))


@pytest.mark.django_db
def test_cheapest_price_per_customer(rf, regular_user):
    shop = get_default_shop()
    supplier = get_default_supplier(shop)
    prices = [100, 20, 50, 80, 90]

    anon_contact = AnonymousContact()
    gold_club_group = ContactGroup.objects.create(name="gold club", shop=shop)
    regular_contact = get_person_contact(regular_user)
    regular_contact.groups.add(gold_club_group)

    request = rf.get("/")
    parent = init_test(request, shop, prices)

    # Let's create extra children available only for certain group
    custom_price_for_gold_club = 3.5
    super_child = create_product("child-super", shop=shop, supplier=supplier, default_price=custom_price_for_gold_club)
    super_child_shop_product = super_child.get_shop_instance(shop)
    super_child_shop_product.visibility_limit = ProductVisibility.VISIBLE_TO_GROUPS
    super_child_shop_product.save()
    super_child_shop_product.visibility_groups.add(gold_club_group)

    super_child.link_to_parent(parent)

    price = shop.create_price

    # Now anon contact should get cheapest price 20
    request = rf.get("/")
    apply_request_middleware(request)
    request.shop = shop
    request.customer = anon_contact
    assert parent.get_cheapest_child_price(request) == price(min(prices))

    # Regular user should be able to get the cheapest price from the special product
    request = rf.get("/")
    apply_request_middleware(request)
    request.shop = shop
    request.customer = regular_contact
    assert parent.get_cheapest_child_price(request) == price(3.5)

    # Lets remove regular user from special group and see the cheapest go price go back to 20
    regular_contact.groups.remove(gold_club_group)
    request = rf.get("/")
    apply_request_middleware(request)
    request.shop = shop
    request.customer = regular_contact
    assert parent.get_cheapest_child_price(request) == price(20)
