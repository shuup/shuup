# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from six import iteritems

from shuup import configuration
from shuup.core.models import ShopProduct
from shuup.utils.i18n import format_money

from .constants import ORDER_MIN_TOTAL_CONFIG_KEY


class OrderSourceMinTotalValidator(object):
    @classmethod
    def get_validation_errors(cls, order_source):
        # check for the minimum sum of order total
        min_total = configuration.get(order_source.shop, ORDER_MIN_TOTAL_CONFIG_KEY, Decimal(0))

        if order_source.shop.prices_include_tax:
            total = order_source.taxful_total_price.value
        else:
            total = order_source.taxless_total_price.value

        if total < min_total:
            min_total_price = format_money(order_source.shop.create_price(min_total))
            msg = _("The total price should be greater than {} to be ordered.").format(min_total_price)
            yield ValidationError(msg, code="order_total_too_low")


class OrderSourceMethodsUnavailabilityReasonsValidator(object):
    @classmethod
    def get_validation_errors(cls, order_source):
        shipping_method = order_source.shipping_method
        payment_method = order_source.payment_method

        if shipping_method:
            for error in shipping_method.get_unavailability_reasons(source=order_source):
                yield error

        if payment_method:
            for error in payment_method.get_unavailability_reasons(source=order_source):
                yield error


class OrderSourceSupplierValidator(object):
    @classmethod
    def get_validation_errors(cls, order_source):
        for supplier in order_source._get_suppliers():
            for product, quantity in iteritems(order_source._get_products_and_quantities(supplier)):
                try:
                    shop_product = product.get_shop_instance(shop=order_source.shop)
                except ShopProduct.DoesNotExist:
                    msg = _("%s is not available in this shop.") % product.name
                    yield ValidationError(msg, code="product_not_available_in_shop")
                    continue

                for error in shop_product.get_orderability_errors(
                    supplier=supplier, quantity=quantity, customer=order_source.customer
                ):
                    error.message = "%s: %s" % (product.name, error.message)
                    yield error
