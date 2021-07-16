# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _

from shuup.core.fields import MoneyValueField
from shuup.utils.properties import MoneyPropped, PriceProperty


class ProductCatalogPrice(MoneyPropped, models.Model):
    product = models.ForeignKey(
        "shuup.Product", related_name="catalog_products", on_delete=models.CASCADE, editable=False
    )
    shop = models.ForeignKey("shuup.Shop", related_name="catalog_products", on_delete=models.CASCADE, editable=False)
    supplier = models.ForeignKey(
        "shuup.Supplier", related_name="catalog_products", on_delete=models.CASCADE, editable=False
    )
    contact_group = models.ForeignKey(
        "shuup.ContactGroup", related_name="catalog_products", on_delete=models.CASCADE, null=True, editable=False
    )
    contact = models.ForeignKey(
        "shuup.Contact", related_name="catalog_products", on_delete=models.CASCADE, null=True, editable=False
    )
    price = PriceProperty("price_value", "shop.currency", "shop.prices_include_tax")
    price_value = MoneyValueField(editable=False, verbose_name=_("price"), help_text=_("The indexed product price"))
    discounted_price = PriceProperty("discounted_price_value", "shop.currency", "shop.prices_include_tax")
    discounted_price_value = MoneyValueField(
        editable=False,
        verbose_name=_("discounted price"),
        help_text=_("The indexed discounted product price."),
        null=True,
    )
    is_available = models.BooleanField(
        verbose_name=_("is available"),
        default=False,
        db_index=True,
        editable=False,
        help_text=_("Whether the product is available for purchasing. This status is managed by the supplier module."),
    )

    def __str__(self):
        return f"{self.product} ({self.shop}, {self.supplier}) = {self.price}"

    class Meta:
        unique_together = ("product", "shop", "supplier", "contact_group", "contact")
        indexes = [
            models.Index(fields=["product", "shop", "supplier", "is_available"]),
            models.Index(fields=["product", "shop", "supplier", "contact", "is_available"]),
            models.Index(fields=["product", "shop", "supplier", "contact_group", "is_available"]),
            models.Index(fields=["product", "shop", "supplier", "contact_group", "contact", "is_available"]),
        ]
