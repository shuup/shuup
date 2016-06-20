# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from django.utils.encoding import force_text

from shoop.campaigns.models import BasketCampaign, CatalogCampaign
from shoop.campaigns.models.basket_conditions import BasketTotalProductAmountCondition, ProductsInBasketCondition
from shoop.campaigns.models.basket_line_effects import FreeProductLine
from shoop.campaigns.models.catalog_filters import (
    CatalogFilter, CategoryFilter, ProductFilter, ProductTypeFilter
)
from shoop.campaigns.models.context_conditions import ContactGroupCondition
from shoop.campaigns.models.product_effects import ProductDiscountAmount
from shoop.core.models import Category, ShopProduct, OrderLineType
from shoop.core.order_creator._source import LineSource
from shoop.front.basket import get_basket
from shoop.testing.factories import create_product, get_default_category, get_default_supplier
from shoop_tests.campaigns import initialize_test
from shoop_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_multiple_effects_work(rf):
    request, shop, group = initialize_test(rf, False)

    basket = get_basket(request)
    supplier = get_default_supplier()

    single_product_price = "50"

    first_product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    basket.add_product(supplier=supplier, shop=shop, product=first_product, quantity=2)
    basket.save()

    second_product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)
    third_product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=single_product_price)

    rule = ProductsInBasketCondition.objects.create(quantity=2)
    rule.products.add(first_product)

    campaign = BasketCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(rule)

    effect1 = FreeProductLine.objects.create(campaign=campaign, quantity=2)
    effect1.products.add(second_product)

    effect2 = FreeProductLine.objects.create(campaign=campaign, quantity=3)
    effect2.products.add(third_product)

    basket.uncache()
    final_lines = basket.get_final_lines()

    assert len(final_lines) == 3  # first_product, second_product, third_product

    ids = set(x.product.id for x in final_lines if x.product)

    for p in [first_product, second_product, third_product]:
        assert p.id in ids

    line_types = [l.type for l in final_lines]
    assert OrderLineType.DISCOUNT not in line_types

    for line in basket.get_final_lines():
        assert line.type == OrderLineType.PRODUCT
        if line.line_source == LineSource.DISCOUNT_MODULE:
            if line.product == second_product:
                assert line.quantity == 2
            elif line.product == third_product:
                assert line.quantity == 3
            else:
                # this should not be possible
                assert 0 == 1, "Missing free product"


@pytest.mark.django_db
def test_multiple_effects_work2(rf):
    request, shop, group = initialize_test(rf, False)

    original_price = 199
    product = create_product("Just-A-Product-Too", shop, default_price=original_price)

    contact_condition = ContactGroupCondition.objects.create()
    contact_condition.contact_groups = request.customer.groups.all()
    contact_condition.save()

    campaign = CatalogCampaign.objects.create(active=True, shop=shop, name="test", public_name="test")
    campaign.conditions.add(contact_condition)

    first_discount = 10
    second_discount = 15.50

    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=first_discount)
    ProductDiscountAmount.objects.create(campaign=campaign, discount_amount=second_discount)

    price = shop.create_price
    expected_discounted_price = price(original_price - (first_discount + second_discount))
    assert product.get_price_info(request, quantity=1).price == expected_discounted_price
