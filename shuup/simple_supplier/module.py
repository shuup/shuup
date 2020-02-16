# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from shuup.core.models import Product
from shuup.core.signals import stocks_updated
from shuup.core.stocks import ProductStockStatus
from shuup.core.suppliers import BaseSupplierModule
from shuup.core.suppliers.enums import StockAdjustmentType
from shuup.core.utils import context_cache
from shuup.simple_supplier.utils import get_current_stock_value
from shuup.utils.djangoenv import has_installed

from .models import StockAdjustment, StockCount


class SimpleSupplierModule(BaseSupplierModule):
    identifier = "simple_supplier"
    name = "Simple Supplier"

    def get_stock_statuses(self, product_ids):
        stock_counts = (
            StockCount.objects
            .filter(supplier=self.supplier, product_id__in=product_ids)
            .values_list("product_id", "physical_count", "logical_count", "stock_managed")
        )
        values = dict(
            (product_id, (physical_count, logical_count, stock_managed))
            for (product_id, physical_count, logical_count, stock_managed)
            in stock_counts
        )
        null = (0, 0, self.supplier.stock_managed)

        stati = []
        for product_id in product_ids:
            stock_managed = values.get(product_id, null)[2]
            if stock_managed is None:
                stock_managed = self.supplier.stock_manage

            stati.append(ProductStockStatus(
                product_id=product_id,
                physical_count=values.get(product_id, null)[0],
                logical_count=values.get(product_id, null)[1],
                stock_managed=stock_managed
            ))

        return dict((pss.product_id, pss) for pss in stati)

    def adjust_stock(self, product_id, delta, purchase_price=0, created_by=None,
                     type=StockAdjustmentType.INVENTORY):

        stock_count = StockCount.objects.get_or_create(
            supplier=self.supplier,
            product_id=product_id,
        )[0]
        if not stock_count.stock_managed:
            # item doesn't manage stocks
            return

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
        """
        Supplier module update stock should always bump product
        cache and send `shuup.core.signals.stocks_updated` signal.
        """
        supplier_id = self.supplier.pk
        sv, _ = StockCount.objects.get_or_create(supplier_id=supplier_id, product_id=product_id)
        if not sv.stock_managed:
            # item doesn't manage stocks
            return

        # TODO: Consider whether this should be done without a cache table
        values = get_current_stock_value(supplier_id=supplier_id, product_id=product_id)
        sv.logical_count = values["logical_count"]
        sv.physical_count = values["physical_count"]
        latest_event = (
            StockAdjustment.objects
            .filter(supplier=supplier_id, product=product_id, type=StockAdjustmentType.INVENTORY)
            .last())
        if latest_event:
            sv.stock_value_value = latest_event.purchase_price_value * sv.logical_count

        if self.supplier.stock_managed and has_installed("shuup.notify"):
            if sv.alert_limit and sv.physical_count < sv.alert_limit:
                product = Product.objects.filter(id=product_id).first()
                if product:
                    from .notify_events import AlertLimitReached
                    for shop in self.supplier.shops.all():
                        supplier_email = self.supplier.contact_address.email if self.supplier.contact_address else ""
                        shop_email = shop.contact_address.email if shop.contact_address else ""
                        AlertLimitReached(
                            supplier=self.supplier,
                            product=product,
                            shop_email=shop_email,
                            supplier_email=supplier_email
                        ).run(shop=shop)

        sv.save(update_fields=("logical_count", "physical_count", "stock_value_value"))
        context_cache.bump_cache_for_product(Product.objects.get(id=product_id))
        stocks_updated.send(
            type(self), shops=self.supplier.shops.all(), product_ids=[product_id], supplier=self.supplier)
