# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import abc

import six

from shuup.apps.provides import load_module_instances


def get_discount_modules():
    """
    Get a list of configured discount module instances.

    :rtype: list[DiscountModule]
    """
    return load_module_instances("SHUUP_DISCOUNT_MODULES", "discount_module")


class DiscountModule(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def discount_price(self, context, product, price_info):
        """
        Discount given price of given product.

        :param context: Pricing context to operate in
        :type context: shuup.core.pricing.PricingContext
        :param product: Product in question or its id
        :type product: shuup.core.models.Product|int
        :param price_info: Price to discount
        :type price_info: shuup.core.pricing.PriceInfo
        :return: Discounted price
        :rtype: shuup.core.pricing.PriceInfo
        """
        return price_info

    def get_pricing_steps(self, context, product, steps):
        """
        Get discounted pricing steps for given product.

        Base class version just discounts all the given steps with
        `discount_price`, but another module could add more steps and
        should do so, if the module introduces any pricing steps.

        :param context: Pricing context to operate in
        :type context: shuup.core.pricing.PricingContext
        :param product: Product in question or its id
        :type product: shuup.core.models.Product|int
        :type steps: list[PriceInfo]
        :rtype: list[PriceInfo]
        """
        return [
            self.discount_price(context, product, price_info)
            for price_info in steps
        ]

    def discount_prices(self, context, products, price_infos):
        """
        Discount a bunch of prices.

        :param context: Pricing context to operate in
        :type context: shuup.core.pricing.PricingContext
        :param products: Products in question or their ids
        :type products: Iterable[shuup.core.models.Product|int]
        :type price_infos: dict[int,PriceInfo]
        :rtype: dict[int,PriceInfo]
        """
        product_map = {getattr(x, "pk", x): x for x in products}
        return {
            pk: self.discount_price(context, product_map[pk], price_info)
            for (pk, price_info) in six.iteritems(price_infos)
        }

    def get_pricing_steps_for_products(self, context, products, steps):
        """
        Get discounted pricing steps for a bunch of products.

        :param context: Pricing context to operate in
        :type context: shuup.core.pricing.PricingContext
        :param products: Products in question or their ids
        :type products: Iterable[shuup.core.models.Product|int]
        :type steps: dict[int,list[PriceInfo]]
        :rtype: dict[int,list[PriceInfo]]
        """
        pks_and_products = ((getattr(x, "pk", x), x) for x in products)
        return {
            pk: self.get_pricing_steps(context, product, steps[pk])
            for (pk, product) in pks_and_products
        }
