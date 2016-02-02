# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
import random

from django.utils.translation import ugettext_lazy as _

from shoop.campaigns.models.campaigns import BasketCampaign, CatalogCampaign
from shoop.core.models import OrderLineType
from shoop.core.order_creator import OrderSourceModifierModule
from shoop.core.pricing import DiscountModule


class CatalogCampaignModule(DiscountModule):
    identifier = "catalog_campaigns"
    name = _("Campaigns")

    def discount_price(self, context, product, price_info):
        """
        Get the discounted price for context.

        Best discount is selected.
        Minimum price will be selected if the cheapest price is under that.
        """
        create_price = context.shop.create_price
        shop_product = product.get_shop_instance(context.shop)

        best_discount = None
        for campaign in CatalogCampaign.get_matching(context, shop_product):
            price = price_info.price
            if campaign.discount_amount_value:
                price -= create_price(campaign.discount_amount_value)
            else:
                price -= (price * campaign.discount_percentage)

            if best_discount is None:
                best_discount = price

            if price < best_discount:
                best_discount = price

        if best_discount:
            if shop_product.minimum_price and best_discount < shop_product.minimum_price:
                best_discount = shop_product.minimum_price

            if best_discount < create_price("0"):
                best_discount = create_price("0")

            price_info.price = best_discount

        return price_info


class BasketCampaignModule(OrderSourceModifierModule):
    identifier = "basket_campaigns"
    name = _("Campaign Basket Discounts")

    def get_new_lines(self, order_source, lines):
        price_so_far = sum((x.price for x in lines), order_source.zero_price)

        def get_discount_line(campaign, amount, price_so_far):
            new_amount = min(amount, price_so_far)
            price_so_far -= new_amount
            return self._get_campaign_line(campaign, new_amount, order_source)

        best_discount = None
        best_discount_campaign = None
        for campaign in BasketCampaign.get_matching(order_source, lines):
            if campaign.discount_amount:
                discount_amount = campaign.discount_amount
            else:
                discount_amount = order_source.total_price_of_products * campaign.discount_percentage

            # if campaign has coupon, match it to order_source.codes
            if campaign.coupon:
                # campaign was found because discount code matched. This line is always added
                yield get_discount_line(campaign, discount_amount, price_so_far)
            elif best_discount is None or discount_amount > best_discount:
                best_discount = discount_amount
                best_discount_campaign = campaign

        if best_discount is not None:
            yield get_discount_line(best_discount_campaign, best_discount, price_so_far)

    def _get_campaign_line(self, campaign, highest_discount, order_source):
        text = campaign.public_name

        if campaign.coupon:
            text += " (%s %s)" % (_("Coupon Code:"), campaign.coupon.code)
        return order_source.create_line(
            line_id="discount_%s" % str(random.randint(0, 0x7FFFFFFF)),
            type=OrderLineType.DISCOUNT,
            quantity=1,
            discount_amount=campaign.shop.create_price(highest_discount),
            text=text
        )

    def can_use_code(self, order_source, code):
        campaigns = BasketCampaign.objects.filter(active=True, coupon__code=code, coupon__active=True)
        for campaign in campaigns:
            if not campaign.is_available():
                continue
            return campaign.coupon.can_use_code(order_source.customer)
        return False

    def use_code(self, order, code):
        campaigns = BasketCampaign.objects.filter(active=True, coupon__code=code, coupon__active=True)
        for campaign in campaigns:
            campaign.coupon.use(order)
