# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils.translation import ugettext_lazy as _

from shuup.core.excs import NoProductsToShipException
from shuup.core.models import Product
from shuup.core.signals import stocks_updated
from shuup.core.stocks import ProductStockStatus
from shuup.core.suppliers import BaseSupplierModule
from shuup.core.suppliers.enums import StockAdjustmentType
from shuup.core.tasks import run_task
from shuup.core.utils import context_cache
from shuup.simple_supplier.utils import get_current_stock_value
from shuup.utils.django_compat import force_text
from shuup.utils.djangoenv import has_installed

from .models import StockAdjustment, StockCount


class SimpleSupplierModule(BaseSupplierModule):
    identifier = "simple_supplier"
    name = _("Simple Supplier")

    def get_orderability_errors(self, shop_product, quantity, customer, *args, **kwargs):
        """
        :param shop_product: Shop Product.
        :type shop_product: shuup.core.models.ShopProduct
        :param quantity: Quantity to order.
        :type quantity: decimal.Decimal
        :param customer: Contact.
        :type user: django.contrib.auth.models.AbstractUser
        :rtype: iterable[ValidationError]
        """
        if shop_product.product.kind not in self.get_supported_product_kinds_values():
            return

        stock_status = self.get_stock_status(shop_product.product_id)

        backorder_maximum = shop_product.backorder_maximum
        if stock_status.error:
            yield ValidationError(stock_status.error, code="stock_error")

        if self.supplier.stock_managed and stock_status.stock_managed:
            if backorder_maximum is not None and quantity > stock_status.logical_count + backorder_maximum:
                yield ValidationError(
                    stock_status.message or _("Error! Insufficient quantity in stock."), code="stock_insufficient"
                )

    def get_stock_statuses(self, product_ids, *args, **kwargs):
        stock_counts = (
            Product.objects.filter(
                pk__in=product_ids,
                simple_supplier_stock_count__supplier=self.supplier,
                kind__in=self.get_supported_product_kinds_values(),
            )
            .annotate(
                physical_count=F("simple_supplier_stock_count__physical_count"),
                logical_count=F("simple_supplier_stock_count__logical_count"),
                stock_managed=F("simple_supplier_stock_count__stock_managed"),
            )
            .values_list("pk", "physical_count", "logical_count", "stock_managed")
        )

        values = dict(
            (product_id, (physical_count or 0, logical_count or 0, stock_managed or False))
            for (product_id, physical_count, logical_count, stock_managed) in stock_counts
        )
        null = (0, 0, self.supplier.stock_managed)

        stati = []
        for product_id in product_ids:
            stock_managed = values.get(product_id, null)[2]
            if stock_managed is None:
                stock_managed = self.supplier.stock_manage

            stati.append(
                ProductStockStatus(
                    product_id=product_id,
                    physical_count=values.get(product_id, null)[0],
                    logical_count=values.get(product_id, null)[1],
                    stock_managed=stock_managed,
                )
            )

        return dict((pss.product_id, pss) for pss in stati)

    def adjust_stock(
        self, product_id, delta, purchase_price=0, created_by=None, type=StockAdjustmentType.INVENTORY, *args, **kwargs
    ):
        stock_count = StockCount.objects.select_related("product").get_or_create(
            supplier=self.supplier,
            product_id=product_id,
        )[0]
        if not stock_count.stock_managed or stock_count.product.kind not in self.get_supported_product_kinds_values():
            # item doesn't manage stocks
            return {}

        adjustment = StockAdjustment.objects.create(
            supplier=self.supplier,
            product_id=product_id,
            delta=delta,
            purchase_price_value=purchase_price,
            created_by=created_by,
            type=type,
        )
        self.update_stock(product_id)
        return adjustment

    def update_stock(self, product_id, *args, **kwargs):
        """
        Supplier module update stock should always bump product
        cache and send `shuup.core.signals.stocks_updated` signal.
        """
        supplier_id = self.supplier.pk
        sv, _ = StockCount.objects.select_related("product").get_or_create(
            supplier_id=supplier_id, product_id=product_id
        )

        # kind not supported
        if sv.product.kind not in self.get_supported_product_kinds_values():
            return

        # item doesn't manage stocks
        if not sv.stock_managed:
            # make sure to index products either way
            run_task("shuup.simple_supplier.tasks.index_product", product=product_id, supplier=self.supplier.pk)
            return

        values = get_current_stock_value(supplier_id=supplier_id, product_id=product_id)
        sv.logical_count = values["logical_count"]
        sv.physical_count = values["physical_count"]
        latest_event = StockAdjustment.objects.filter(
            supplier=supplier_id, product=product_id, type=StockAdjustmentType.INVENTORY
        ).last()
        if latest_event:
            sv.stock_value_value = latest_event.purchase_price_value * sv.logical_count

        # TODO: get rid of this and move to shuup.notify app instead, through signals
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
                            supplier_email=supplier_email,
                        ).run(shop=shop)

        sv.save(update_fields=("logical_count", "physical_count", "stock_value_value"))
        context_cache.bump_cache_for_product(product_id)
        stocks_updated.send(
            type(self), shops=self.supplier.shops.all(), product_ids=[product_id], supplier=self.supplier
        )
        run_task("shuup.simple_supplier.tasks.index_product", product=product_id, supplier=self.supplier.pk)

    def ship_products(self, shipment, product_quantities, *args, **kwargs):
        # stocks are managed, do stocks check
        if self.supplier.stock_managed:
            insufficient_stocks = {}

            for product, quantity in product_quantities.items():
                if quantity > 0 and product.kind in self.get_supported_product_kinds_values():
                    stock_status = self.get_stock_status(product.pk)
                    if stock_status.stock_managed and stock_status.physical_count < quantity:
                        insufficient_stocks[product] = stock_status.physical_count

            if insufficient_stocks:
                formatted_counts = [
                    _("%(name)s (physical stock: %(quantity)s)")
                    % {"name": force_text(name), "quantity": force_text(int(quantity))}
                    for (name, quantity) in insufficient_stocks.items()
                ]
                raise NoProductsToShipException(
                    _("Insufficient physical stock count for the following products: `%(product_counts)s`.")
                    % {"product_counts": ", ".join(formatted_counts)}
                )

        for product, quantity in product_quantities.items():
            if quantity == 0 or product.kind not in self.get_supported_product_kinds_values():
                continue

            sp = shipment.products.create(product=product, quantity=quantity)
            sp.cache_values()
            sp.save()

        shipment.cache_values()
        shipment.save()
