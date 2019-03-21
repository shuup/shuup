# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import random

from django.utils.translation import ugettext_lazy as _

from shuup.campaigns.models.campaigns import (
    BasketCampaign, CatalogCampaign, CouponUsage
)
from shuup.core.models import OrderLineType, ShopProduct
from shuup.core.order_creator import OrderSourceModifierModule
from shuup.core.order_creator._source import LineSource
from shuup.core.pricing import DiscountModule


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
        try:
            shop_product = product.get_shop_instance(context.shop)
        except ShopProduct.DoesNotExist:
            return price_info

        best_discount = None
        for campaign in CatalogCampaign.get_matching(context, shop_product):
            price = price_info.price
            # get first matching effect
            for effect in campaign.effects.all():
                price -= effect.apply_for_product(context=context, product=product, price_info=price_info)

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
        matching_campaigns = BasketCampaign.get_matching(order_source, lines)

        for line in self._handle_line_effects(matching_campaigns, order_source, lines):
            yield line

        # total discounts must be run after line effects since lines can be changed in place
        for line in self._handle_total_discount_effects(matching_campaigns, order_source, lines):
            yield line

    def _get_campaign_line(self, campaign, highest_discount, order_source):
        text = campaign.public_name

        if campaign.coupon:
            text += " (%s %s)" % (_("Coupon Code:"), campaign.coupon.code)

        return order_source.create_line(
            line_id="discount_%s" % str(random.randint(0, 0x7FFFFFFF)),
            type=OrderLineType.DISCOUNT,
            quantity=1,
            discount_amount=campaign.shop.create_price(highest_discount),
            text=text,
            line_source=LineSource.DISCOUNT_MODULE
        )

    def can_use_code(self, order_source, code):
        campaigns = BasketCampaign.objects.filter(
            active=True, shop=order_source.shop, coupon__code__iexact=code, coupon__active=True)
        for campaign in campaigns:
            if not campaign.is_available():
                continue
            return campaign.coupon.can_use_code(order_source.customer)
        return False

    def use_code(self, order, code):
        campaigns = BasketCampaign.objects.filter(
            active=True, shop=order.shop, coupon__code__iexact=code, coupon__active=True)
        for campaign in campaigns:
            campaign.coupon.use(order)

    def clear_codes(self, order):
        CouponUsage.objects.filter(order=order).delete()

    def _handle_total_discount_effects(self, matching_campaigns, order_source, original_lines):
        price_so_far = sum((x.price for x in original_lines), order_source.zero_price)

        def get_discount_line(campaign, amount, price_so_far):
            new_amount = min(amount, price_so_far)
            price_so_far -= new_amount
            return self._get_campaign_line(campaign, new_amount, order_source)

        best_discount_for_supplier = {}
        lines = []
        for campaign in matching_campaigns:
            campaign_supplier = campaign.supplier if hasattr(campaign, "supplier") and campaign.supplier else None

            for effect in campaign.discount_effects.all():
                discount_amount = min(price_so_far, effect.apply_for_basket(order_source=order_source))

                # if campaign has coupon, match it to order_source.codes
                if campaign.coupon:
                    # campaign was found because discount code matched. This line is always added
                    lines.append(get_discount_line(campaign, discount_amount, price_so_far))

                else:
                    best_discount = best_discount_for_supplier.get(campaign_supplier)
                    if not best_discount or discount_amount > best_discount["discount_amount"]:
                        best_discount_for_supplier[campaign_supplier] = dict(
                            discount_amount=discount_amount,
                            campaign=campaign
                        )

        for supplier, best_discount_info in best_discount_for_supplier.items():
            lines.append(
                get_discount_line(best_discount_info["campaign"], best_discount_info["discount_amount"], price_so_far))
        return lines

    def _handle_line_effects(self, matching_campaigns, order_source, original_lines):
        lines = []
        for campaign in matching_campaigns:
            for effect in campaign.line_effects.all():
                lines += effect.get_discount_lines(order_source=order_source, original_lines=original_lines)
        return lines
