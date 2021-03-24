# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import pytest
from decimal import Decimal
from django.db import IntegrityError

from shuup.campaigns.admin_module.forms import BasketCampaignForm
from shuup.campaigns.models.basket_conditions import (
    BasketTotalAmountCondition,
    BasketTotalProductAmountCondition,
    CategoryProductsBasketCondition,
    ProductsInBasketCondition,
)
from shuup.campaigns.models.basket_effects import BasketDiscountAmount, BasketDiscountPercentage
from shuup.campaigns.models.basket_line_effects import DiscountFromCategoryProducts
from shuup.campaigns.models.campaigns import BasketCampaign, Coupon, CouponUsage
from shuup.core.models import Category, OrderLineType, Shop, ShopProduct, ShopStatus, Supplier
from shuup.core.order_creator import OrderCreator
from shuup.front.basket import get_basket
from shuup.front.basket.commands import handle_add_campaign_code, handle_remove_campaign_code
from shuup.testing.factories import (
    CategoryFactory,
    create_product,
    get_default_product,
    get_default_shop,
    get_default_supplier,
    get_shipping_method,
)
from shuup_tests.campaigns import initialize_test
from shuup_tests.core.test_order_creator import seed_source
from shuup_tests.utils import printable_gibberish


@pytest.mark.django_db
def test_basket_campaign_with_multiple_supppliers(rf):
    request, shop, group = initialize_test(rf, False)
    supplier1 = Supplier.objects.create(identifier="1")
    supplier2 = Supplier.objects.create(identifier="2")
    supplier1.shops.add(shop)
    supplier2.shops.add(shop)

    price = shop.create_price
    basket = get_basket(request)

    single_product_price = "50"
    discount_amount_supplier1 = "10"
    discount_amount_supplier2 = "40"

    product1 = create_product("product1", shop=shop, supplier=supplier1, default_price=single_product_price)
    product2 = create_product("product2", shop=shop, supplier=supplier2, default_price=single_product_price)

    basket.add_product(supplier=supplier1, shop=shop, product=product1, quantity=1)
    basket.add_product(supplier=supplier2, shop=shop, product=product2, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    assert basket.product_count == 2
    assert basket.total_price.value == 100

    # Create campaign for supplier one
    basket_rule1 = ProductsInBasketCondition.objects.create(quantity=1)
    basket_rule1.products.add(product1)

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", active=True, supplier=supplier1
    )
    campaign.conditions.add(basket_rule1)
    campaign.save()
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount_supplier1)

    basket.uncache()
    lines = basket.get_final_lines()
    assert len(lines) == 4
    assert basket.total_price.value == 90  # 10d discount from the supplier1 product
    line = _get_discount_line(lines, 10)
    assert line.supplier == supplier1

    # Create campaign for supplier two
    basket_rule2 = ProductsInBasketCondition.objects.create(quantity=1)
    basket_rule2.products.add(product2)

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", active=True, supplier=supplier2
    )
    campaign.conditions.add(basket_rule2)
    campaign.save()
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount_supplier2)

    basket.uncache()
    lines = basket.get_final_lines()
    assert len(lines) == 5
    assert basket.total_price.value == 50  # -10d - 40d from 100d
    line = _get_discount_line(lines, 40)
    assert line.supplier == supplier2


@pytest.mark.django_db
def test_basket_campaign_with_multiple_supppliers_sharing_product(rf):
    request, shop, group = initialize_test(rf, False)
    supplier1 = Supplier.objects.create(identifier="1")
    supplier2 = Supplier.objects.create(identifier="2")
    supplier1.shops.add(shop)
    supplier2.shops.add(shop)

    price = shop.create_price
    basket = get_basket(request)

    single_product_price = "50"
    discount_amount = "10"

    product = create_product("product1", shop=shop, supplier=supplier1, default_price=single_product_price)
    shop_product = product.get_shop_instance(shop)
    shop_product.suppliers.add(supplier2)

    basket.add_product(supplier=supplier1, shop=shop, product=product, quantity=1)
    basket.add_product(supplier=supplier2, shop=shop, product=product, quantity=1)
    basket.shipping_method = get_shipping_method(shop=shop)
    basket.save()

    assert basket.product_count == 2
    assert basket.total_price.value == 100

    # Create campaign for supplier one
    basket_rule = ProductsInBasketCondition.objects.create(quantity=2)
    basket_rule.products.add(product)
    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", active=True, supplier=supplier1
    )
    campaign.conditions.add(basket_rule)
    campaign.save()
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount)

    basket.uncache()
    assert len(basket.get_final_lines()) == 3  # +1 for shipping line
    # No disocunt since not enough products in basket for supplier 1
    assert basket.total_price.value == 100

    # Let's add second product for supplier 2
    # We still should not get discount
    basket.add_product(supplier=supplier2, shop=shop, product=product, quantity=1)
    basket.save()
    basket.uncache()
    assert len(basket.get_final_lines()) == 3
    # No disocunt since not enough products in basket for supplier 1
    assert basket.total_price.value == 150

    # Let's add second produdct for supplier one and now we should
    # finally get that 10d discount
    basket.add_product(supplier=supplier1, shop=shop, product=product, quantity=1)
    basket.save()
    basket.uncache()
    assert len(basket.get_final_lines()) == 4  # +1 for discount line
    # No disocunt since not enough products in basket for supplier 1
    assert basket.total_price.value == 190

    # For sake of it lets do second discount for supplier 2 after 3 products
    discount_amount_2 = "40"

    # Create campaign for supplier two
    basket_rule2 = ProductsInBasketCondition.objects.create(quantity=3)
    basket_rule2.products.add(product)

    campaign = BasketCampaign.objects.create(
        shop=shop, public_name="test", name="test", active=True, supplier=supplier2
    )
    campaign.conditions.add(basket_rule2)
    campaign.save()
    BasketDiscountAmount.objects.create(campaign=campaign, discount_amount=discount_amount_2)

    assert len(basket.get_final_lines()) == 4
    # No disocunt since not enough products in basket for supplier 1
    assert basket.total_price.value == 190

    # Let's add third produdct for supplier two and now we should
    # finally get that 10d discount
    basket.add_product(supplier=supplier2, shop=shop, product=product, quantity=1)
    basket.save()
    basket.uncache()
    assert len(basket.get_final_lines()) == 5  # +1 for discount line
    # No disocunt since not enough products in basket for supplier 1
    assert basket.total_price.value == 200


def _get_discount_line(lines, discount_amount_value):
    for line in lines:
        if "discount" in line.line_id and line.discount_amount.value == Decimal(discount_amount_value):
            return line
