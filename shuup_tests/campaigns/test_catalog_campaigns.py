# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import datetime
import decimal
import json
import pytest
from decimal import Decimal
from django.test import override_settings
from django.test.client import RequestFactory
from django.utils.timezone import now
from django.utils.translation import activate

from shuup.admin.modules.orders.views.edit import OrderEditView
from shuup.campaigns.models.campaigns import CatalogCampaign
from shuup.campaigns.models.catalog_filters import CategoryFilter, ProductFilter, ProductTypeFilter
from shuup.campaigns.models.context_conditions import ContactGroupCondition
from shuup.campaigns.models.product_effects import ProductDiscountAmount, ProductDiscountPercentage
from shuup.core.models import Category, ProductType, Shop, ShopProduct, ShopStatus
from shuup.testing.factories import create_product, get_default_customer_group, get_default_shop
from shuup.testing.utils import apply_request_middleware
from shuup_tests.campaigns import initialize_test


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_campaign_creation():
    rf = RequestFactory()
    activate("en")
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    condition = ContactGroupCondition.objects.create()
    condition.contact_groups.set(request.customer.groups.all())
    condition.save()

    assert condition.values.first() == request.customer.groups.first()

    condition.values.set(request.customer.groups.all())
    condition.save()
    assert condition.values.first() == request.customer.groups.first()

    category_filter = CategoryFilter.objects.create()
    category_filter.categories.add(cat)
    category_filter.save()

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(condition)
    campaign.filters.add(category_filter)
    campaign.save()
    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=20)

    # Make sure disabling campaign disables it filters and conditions
    assert campaign.filters.filter(active=True).exists()
    assert campaign.conditions.filter(active=True).exists()
    campaign.active = False
    campaign.save()
    assert not campaign.filters.filter(active=True).exists()
    assert not campaign.conditions.filter(active=True).exists()


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_condition_doesnt_match():
    rf = RequestFactory()
    activate("en")
    request, shop, group = initialize_test(rf, False)
    condition = ContactGroupCondition.objects.create()
    condition.contact_groups.set([get_default_customer_group()])
    condition.save()

    request.customer = None

    assert not condition.matches(request)


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_condition_affects_price():
    rf = RequestFactory()
    activate("en")
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    contact_condition = ContactGroupCondition.objects.create()
    contact_condition.contact_groups.set(request.customer.groups.all())
    contact_condition.save()

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(contact_condition)
    campaign.save()

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=20)

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=199)
    assert product.get_price_info(request, quantity=2).price == price(179) * 2


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_filter_affects_price():
    rf = RequestFactory()
    activate("en")
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    category_filter = CategoryFilter.objects.create()
    category_filter.categories.add(cat)
    category_filter.save()

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.filters.add(category_filter)
    campaign.save()

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=20)

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=199)
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()
    assert product.get_price_info(request, quantity=1).price == price(179)


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_campaign_all_rules_must_match1():
    rf = RequestFactory()
    activate("en")
    discount_amount = "20.53"
    original_price = "199.20"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1 = ContactGroupCondition.objects.create()
    rule1.contact_groups.set(request.customer.groups.all())
    rule1.save()

    rule2 = CategoryFilter.objects.create()
    rule2.categories.add(cat)
    rule2.save()

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount)

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    price = shop.create_price
    # price should not be discounted because the request.category is faulty
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()
    # now the category is set, so both rules match, disconut should be given
    assert product.get_price_info(request, quantity=1).price == (price(original_price) - price(discount_amount))


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_percentage_campaigns():
    rf = RequestFactory()
    activate("en")
    discount_percentage = "0.14"
    original_price = "123.47"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1 = ContactGroupCondition.objects.create()
    rule1.contact_groups.set(request.customer.groups.all())
    rule1.save()

    rule2 = CategoryFilter.objects.create()
    rule2.categories.add(cat)
    rule2.save()
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    cdp = ProductDiscountPercentage.objects.create(campaign=campaign, discount_percentage=discount_percentage)

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    price = shop.create_price
    # price should not be discounted because the request.category is faulty
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()
    # now the category is set, so both rules match, discount should be given
    discounted_price = price(original_price) - (price(original_price) * Decimal(cdp.value))
    assert product.get_price_info(request, quantity=1).price == discounted_price


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_only_best_price_affects():
    rf = RequestFactory()
    activate("en")
    discount_amount = "20.53"
    original_price = "199.20"
    best_discount_amount = "40.00"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")

    rule1, rule2 = create_condition_and_filter(cat, request)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount)

    rule3, rule4 = create_condition_and_filter(cat, request)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(rule3)
    campaign.filters.add(rule4)
    campaign.save()

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=best_discount_amount)

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    price = shop.create_price
    # price should not be discounted because the request.category is faulty
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()
    # now the category is set, so both rules match, discount should be given
    assert product.get_price_info(request, quantity=1).price == (price(original_price) - price(best_discount_amount))


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_minimum_price_is_forced():
    rf = RequestFactory()
    activate("en")
    discount_amount = "20.53"
    original_price = "199.20"
    allowed_minimum_price = "190.20"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1, rule2 = create_condition_and_filter(cat, request)
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount)

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)
    shop_product = product.get_shop_instance(shop)
    shop_product.minimum_price = price(allowed_minimum_price)
    shop_product.save()

    # price should not be discounted because the request.category is faulty
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    shop_product.categories.add(cat)
    shop_product.save()
    # now the category is set, so both rules match, discount should be given
    assert product.get_price_info(request, quantity=1).price == shop_product.minimum_price


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_price_cannot_be_under_zero():
    rf = RequestFactory()
    activate("en")
    discount_amount = "200"
    original_price = "199.20"

    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1, rule2 = create_condition_and_filter(cat, request)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(rule1)
    campaign.filters.add(rule2)
    campaign.save()

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount)

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(cat)
    shop_product.save()

    assert product.get_price_info(request, quantity=1).price == price("0")


def create_condition_and_filter(cat, request):
    rule1 = ContactGroupCondition.objects.create()
    rule1.contact_groups.set(request.customer.groups.all())
    rule1.save()
    rule2 = CategoryFilter.objects.create()
    rule2.categories.add(cat)
    rule2.save()
    return rule1, rule2


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_start_end_dates():
    rf = RequestFactory()
    activate("en")
    original_price = "180"
    discounted_price = "160"
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1, rule2 = create_condition_and_filter(cat, request)

    discount_amount = 20

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    campaign.conditions.add(rule1)
    campaign.save()

    ProductDiscountAmount.objects.create(discount_amount=discount_amount, campaign=campaign)

    price = shop.create_price

    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    today = now()

    # starts in future
    campaign.start_datetime = today + datetime.timedelta(days=2)
    campaign.save()
    assert not campaign.is_available()
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    # has already started
    campaign.start_datetime = today - datetime.timedelta(days=2)
    campaign.save()
    assert product.get_price_info(request, quantity=1).price == price(discounted_price)

    # already ended
    campaign.end_datetime = today - datetime.timedelta(days=1)
    campaign.save()
    assert not campaign.is_available()
    assert product.get_price_info(request, quantity=1).price == price(original_price)

    # not ended yet
    campaign.end_datetime = today + datetime.timedelta(days=1)
    campaign.save()
    assert product.get_price_info(request, quantity=1).price == price(discounted_price)

    # no start datetime
    campaign.start_datetime = None
    campaign.save()
    assert product.get_price_info(request, quantity=1).price == price(discounted_price)

    # no start datetime but ended
    campaign.end_datetime = today - datetime.timedelta(days=1)
    campaign.save()
    assert not campaign.is_available()
    assert product.get_price_info(request, quantity=1).price == price(original_price)


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_availability():
    rf = RequestFactory()
    activate("en")
    request, shop, group = initialize_test(rf, False)
    cat = Category.objects.create(name="test")
    rule1, rule2 = create_condition_and_filter(cat, request)
    discount_amount = "20"
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=False)
    campaign.conditions.add(rule1)
    campaign.save()

    ProductDiscountAmount.objects.create(discount_amount=discount_amount, campaign=campaign)

    assert not campaign.is_available()


@pytest.mark.django_db
def test_admin_order_with_campaign(rf, admin_user):
    with override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"]):
        request, shop, group = initialize_test(rf, False)
        customer = request.customer
        cat = Category.objects.create(name="test")
        rule1, rule2 = create_condition_and_filter(cat, request)
        campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
        campaign.conditions.add(rule1)

        ProductDiscountAmount.objects.create(campaign=campaign, discount_amount="10")
        product = create_product("Just-A-Product-Too", shop, default_price=20)
        shop_product = product.get_shop_instance(shop)
        shop_product.categories.add(cat)

        request = apply_request_middleware(
            rf.get(
                "/",
                {
                    "command": "product_data",
                    "shop_id": shop.id,
                    "customer_id": customer.id,
                    "id": product.id,
                    "quantity": 1,
                },
            ),
            user=admin_user,
            HTTP_HOST=shop.domain,
            shop=shop,
        )
        response = OrderEditView.as_view()(request)
        data = json.loads(response.content.decode("utf8"))
        assert decimal.Decimal(data["unitPrice"]["value"]) == shop.create_price(10).value


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_product_catalog_campaigns():
    shop = get_default_shop()

    product = create_product("test", shop, default_price=20)
    parent_product = create_product("parent", shop, default_price=40)
    no_shop_child = create_product("child-no-shop")
    shop_child = create_product("child-shop", shop, default_price=60)

    shop_child.link_to_parent(parent_product)
    no_shop_child.link_to_parent(parent_product)

    shop_product = product.get_shop_instance(shop)
    parent_shop_product = parent_product.get_shop_instance(shop)
    child_shop_product = shop_child.get_shop_instance(shop)

    cat = Category.objects.create(name="test")
    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)

    # no rules
    assert CatalogCampaign.get_for_product(shop_product).count() == 0
    assert CatalogCampaign.get_for_product(parent_shop_product).count() == 0
    assert CatalogCampaign.get_for_product(child_shop_product).count() == 0

    # category filter that doesn't match
    cat_filter = CategoryFilter.objects.create()
    cat_filter.categories.add(cat)
    campaign.filters.add(cat_filter)
    assert CatalogCampaign.get_for_product(shop_product).count() == 0
    assert CatalogCampaign.get_for_product(parent_shop_product).count() == 0
    assert CatalogCampaign.get_for_product(child_shop_product).count() == 0

    for sp in [shop_product, parent_shop_product, child_shop_product]:
        sp.primary_category = cat
        sp.save()
        assert CatalogCampaign.get_for_product(sp).count() == 1
        sp.categories.remove(cat)
        sp.primary_category = None
        sp.save()
        assert CatalogCampaign.get_for_product(sp).count() == 0
        # category filter that matches
        sp.categories.add(cat)
        assert CatalogCampaign.get_for_product(sp).count() == 1

    # create other shop
    shop1 = Shop.objects.create(
        name="testshop", identifier="testshop", status=ShopStatus.ENABLED, public_name="testshop"
    )
    sp = ShopProduct.objects.create(product=product, shop=shop1, default_price=shop1.create_price(200))

    assert product.get_shop_instance(shop1) == sp

    campaign2 = CatalogCampaign.objects.create(shop=shop1, name="test1", active=True)
    cat_filter2 = CategoryFilter.objects.create()
    cat_filter2.categories.add(cat)
    campaign2.filters.add(cat_filter2)
    assert CatalogCampaign.get_for_product(sp).count() == 0

    # add product to this category
    sp.primary_category = cat
    sp.save()

    assert CatalogCampaign.get_for_product(sp).count() == 1  # matches now
    sp.categories.remove(cat)
    sp.primary_category = None
    sp.save()
    assert CatalogCampaign.get_for_product(sp).count() == 0  # no match
    sp.categories.add(cat)

    assert CatalogCampaign.get_for_product(sp).count() == 1  # matches now

    campaign3 = CatalogCampaign.objects.create(shop=shop1, name="test1", active=True)
    cat_filter3 = CategoryFilter.objects.create()
    cat_filter3.categories.add(cat)
    campaign3.filters.add(cat_filter3)

    assert CatalogCampaign.get_for_product(sp).count() == 2  # there are now two matching campaigns in same shop
    assert CatalogCampaign.get_for_product(shop_product).count() == 1  # another campaign matches only once


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_product_catalog_campaigns2():
    shop = get_default_shop()
    product = create_product("test", shop, default_price=20)
    product_type = ProductType.objects.create(name="asdf")
    shop_product = product.get_shop_instance(shop)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    assert CatalogCampaign.get_for_product(shop_product).count() == 0

    type_filter = ProductTypeFilter.objects.create()
    type_filter.product_types.add(product_type)
    campaign.filters.add(type_filter)
    assert CatalogCampaign.get_for_product(shop_product).count() == 0
    type_filter.product_types.add(product.type)
    assert type_filter.matches(shop_product)
    assert CatalogCampaign.get_for_product(shop_product).count() == 1
    product.type = product_type
    product.save()
    assert type_filter.matches(shop_product)
    assert CatalogCampaign.get_for_product(shop_product).count() == 1
    type_filter.product_types.remove(product_type)
    assert not type_filter.matches(shop_product)
    assert CatalogCampaign.get_for_product(shop_product).count() == 0


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_product_catalog_campaigns3():
    shop = get_default_shop()
    product = create_product("test", shop, default_price=20)
    shop_product = product.get_shop_instance(shop)

    campaign = CatalogCampaign.objects.create(shop=shop, name="test", active=True)
    assert CatalogCampaign.get_for_product(shop_product).count() == 0

    type_filter = ProductFilter.objects.create()
    type_filter.products.add(product)
    campaign.filters.add(type_filter)
    assert CatalogCampaign.get_for_product(shop_product).count() == 1
