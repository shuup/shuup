# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.

import pytest
from decimal import Decimal
from django.test import override_settings
from django.test.client import RequestFactory

from shuup.campaigns.models import BasketCampaign, BasketLineEffect, CatalogCampaign
from shuup.campaigns.models.basket_conditions import CategoryProductsBasketCondition, ComparisonOperator
from shuup.campaigns.models.basket_line_effects import DiscountFromCategoryProducts, DiscountFromProduct
from shuup.campaigns.models.catalog_filters import ProductFilter
from shuup.campaigns.models.product_effects import ProductDiscountPercentage
from shuup.front.basket import get_basket
from shuup.testing.factories import create_product, get_default_category, get_default_supplier, get_shipping_method
from shuup_tests.campaigns import initialize_test
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
@override_settings(SHUUP_DISCOUNT_MODULES=["customer_group_discount", "catalog_campaigns"])
def test_multiple_campaigns_cheapest_price():
    rf = RequestFactory()
    request, shop, group = initialize_test(rf, False)
    price = shop.create_price
    product_price = "100"
    discount_percentage = "0.30"
    discount_amount_value = "10"
    total_discount_amount = "50"

    expected_total = price(product_price) - (Decimal(discount_percentage) * price(product_price))
    matching_expected_total = price(product_price) - price(total_discount_amount)

    category = get_default_category()
    supplier = get_default_supplier(shop)
    product = create_product(printable_gibberish(), shop=shop, supplier=supplier, default_price=product_price)
    shop_product = product.get_shop_instance(shop)
    shop_product.categories.add(category)

    # create catalog campaign
    catalog_filter = ProductFilter.objects.create()
    catalog_filter.products.add(product)
    catalog_campaign = CatalogCampaign.objects.create(shop=shop, active=True, name="test")
    catalog_campaign.filters.add(catalog_filter)

    cdp = ProductDiscountPercentage.objects.create(campaign=catalog_campaign, discount_percentage=discount_percentage)

    # create basket campaign
    condition = CategoryProductsBasketCondition.objects.create(operator=ComparisonOperator.EQUALS, quantity=1)
    condition.categories.add(category)
    basket_campaign = BasketCampaign.objects.create(shop=shop, public_name="test", name="test", active=True)
    basket_campaign.conditions.add(condition)

    effect = DiscountFromProduct.objects.create(campaign=basket_campaign, discount_amount=discount_amount_value)
    effect.products.add(product)

    # add product to basket
    basket = get_basket(request)
    basket.add_product(supplier=supplier, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)
    final_lines = basket.get_final_lines()
    assert len(final_lines) == 2
    assert basket.total_price == expected_total

    effect.discount_amount = total_discount_amount
    effect.save()
    basket.uncache()
    catalog_campaign.save()  # save to bump caches
    basket_campaign.save()  # save to bump caches

    assert basket.total_price == matching_expected_total  # discount is now bigger than the original

    effect.delete()  # remove effect
    basket.uncache()
    catalog_campaign.save()  # save to bump caches
    basket_campaign.save()  # save to bump caches

    assert BasketLineEffect.objects.count() == 0

    assert basket.total_price == expected_total
    # add new effect
    effect = DiscountFromCategoryProducts.objects.create(
        category=category, campaign=basket_campaign, discount_amount=discount_amount_value
    )
    assert basket.total_price == expected_total

    effect.discount_amount = total_discount_amount
    effect.save()
    basket.uncache()
    catalog_campaign.save()  # save to bump caches
    basket_campaign.save()  # save to bump caches
    assert basket.total_price == matching_expected_total  # discount is now bigger than the original
