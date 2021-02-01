# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from .customer_sales import CustomerSalesReport
from .new_customers import NewCustomersReport
from .product_total_sales import ProductSalesReport
from .refunds import RefundedSalesReport
from .sales import SalesReport
from .sales_per_hour import SalesPerHour
from .shipping import ShippingReport
from .taxes import TaxesReport
from .total_sales import TotalSales

__all__ = [
    "CustomerSalesReport",
    "NewCustomersReport",
    "ProductSalesReport",
    "RefundedSalesReport",
    "SalesPerHour",
    "SalesReport",
    "ShippingReport",
    "TaxesReport",
    "TotalSales",
]
