# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import StockBehavior
from shoop.core.stocks import ProductStockStatus


class BaseSupplierModule(object):
    """
    Base supplier module implementation.
    """

    identifier = None
    name = None

    def __init__(self, supplier, options):
        """
        :type supplier: Supplier
        :type options: dict
        """
        self.supplier = supplier
        self.options = options

    def get_stock_statuses(self, product_ids):
        """
        :param product_ids: Iterable of product IDs
        :return: Dict of {product_id: ProductStockStatus}
        :rtype: dict[int, shoop.core.stocks.ProductStockStatus]
        """
        return dict((
            product_id,
            ProductStockStatus(product_id=product_id, logical_count=0, physical_count=0)
        ) for product_id in product_ids)

    def get_stock_status(self, product_id):
        """
        :param product_id: Product ID
        :type product_id: int
        :rtype: shoop.core.stocks.ProductStockStatus
        """
        return self.get_stock_statuses([product_id])[product_id]

    def get_orderability_errors(self, shop_product, quantity, customer):
        """
        :param shop_product: Shop Product
        :type shop_product: shoop.core.models.ShopProduct
        :param quantity: Quantity to order
        :type quantity: decimal.Decimal
        :param customer: Contact
        :type user: django.contrib.auth.models.AbstractUser
        :rtype: iterable[ValidationError]
        """
        stock_status = self.get_stock_status(shop_product.product_id)
        if stock_status.error:
            yield ValidationError(stock_status.error, code="stock_error")
        if shop_product.product.stock_behavior == StockBehavior.STOCKED:
            if quantity >= stock_status.logical_count:
                yield ValidationError(stock_status.message or _(u"Insufficient stock"), code="stock_insufficient")

    def adjust_stock(self, product_id, delta, created_by=None):
        raise NotImplementedError("Not implemented in BaseSupplierModule")

    def update_stock(self, product_id):
        pass  # no-op in BaseSupplierModule

    def update_stocks(self, product_ids):
        # Naive default implementation; smarter modules can do something better
        for product_id in product_ids:
            self.update_stock(product_id)
