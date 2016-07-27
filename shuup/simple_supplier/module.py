# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.stocks import ProductStockStatus
from shuup.core.suppliers import BaseSupplierModule
from shuup.core.suppliers.enums import StockAdjustmentType
from shuup.simple_supplier.utils import get_current_stock_value

from .models import StockAdjustment, StockCount


class SimpleSupplierModule(BaseSupplierModule):
    identifier = "simple_supplier"
    name = "Simple Supplier"

    def get_stock_statuses(self, product_ids):
        stock_counts = (
            StockCount.objects
            .filter(supplier=self.supplier, product_id__in=product_ids)
            .values_list("product_id", "physical_count", "logical_count")
        )
        values = dict(
            (product_id, (physical_count, logical_count))
            for (product_id, physical_count, logical_count)
            in stock_counts
        )
        null = (0, 0)
        stati = [ProductStockStatus(
            product_id=product_id,
            physical_count=values.get(product_id, null)[0],
            logical_count=values.get(product_id, null)[1]
        ) for product_id in product_ids]
        return dict((pss.product_id, pss) for pss in stati)

    def adjust_stock(self, product_id, delta, purchase_price=0, created_by=None,
                     type=StockAdjustmentType.INVENTORY):
        adjustment = StockAdjustment.objects.create(
            supplier=self.supplier,
            product_id=product_id,
            delta=delta,
            purchase_price_value=purchase_price,
            created_by=created_by,
            type=type
        )
        self.update_stock(product_id)
        return adjustment

    def update_stock(self, product_id):
        supplier_id = self.supplier.pk
        # TODO: Consider whether this should be done without a cache table
        values = get_current_stock_value(supplier_id=supplier_id, product_id=product_id)
        sv, _ = StockCount.objects.get_or_create(supplier_id=supplier_id, product_id=product_id)
        sv.logical_count = values["logical_count"]
        sv.physical_count = values["physical_count"]
        latest_event = (
            StockAdjustment.objects
            .filter(supplier=supplier_id, product=product_id, type=StockAdjustmentType.INVENTORY)
            .last())
        if latest_event:
            sv.stock_value_value = latest_event.purchase_price_value * sv.logical_count
        sv.save(update_fields=("logical_count", "physical_count", "stock_value_value"))
