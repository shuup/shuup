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
    product = models.ForeignKey("shuup.Product", related_name="catalog_prices", on_delete=models.CASCADE)
    shop = models.ForeignKey("shuup.Shop", related_name="catalog_prices", on_delete=models.CASCADE)
    supplier = models.ForeignKey("shuup.Supplier", related_name="catalog_prices", on_delete=models.CASCADE, null=True)
    contact_group = models.ForeignKey(
        "shuup.ContactGroup", related_name="catalog_prices", on_delete=models.CASCADE, null=True
    )
    contact = models.ForeignKey("shuup.Contact", related_name="catalog_prices", on_delete=models.CASCADE, null=True)
    price = PriceProperty("price_value", "shop.currency", "shop.prices_include_tax")
    price_value = MoneyValueField(
        verbose_name=_("price"),
        help_text=_(
            "This is the default individual base unit (or multi-pack) price of the product. "
            "All discounts or coupons will be calculated based off of this price."
        ),
    )
    discounted_price = PriceProperty("discounted_price_value", "shop.currency", "shop.prices_include_tax")
    discounted_price_value = MoneyValueField(
        verbose_name=_("discounted price"), help_text=_("The discounted product price."), null=True
    )

    class Meta:
        unique_together = ("product", "shop", "supplier", "contact_group", "contact")
        indexes = [models.Index(fields=["product", "shop"]), models.Index(fields=["product", "shop", "supplier"])]


class ProductCatalogAvailability(MoneyPropped, models.Model):
    product = models.ForeignKey("shuup.Product", related_name="catalog_availability", on_delete=models.CASCADE)
    shop = models.ForeignKey("shuup.Shop", related_name="catalog_availability", on_delete=models.CASCADE)
    supplier = models.ForeignKey("shuup.Supplier", related_name="catalog_availability", on_delete=models.CASCADE)
    is_available = models.BooleanField(verbose_name=_("is available"), default=False, db_index=True)

    class Meta:
        unique_together = ("product", "shop", "supplier")
        indexes = [models.Index(fields=["product", "shop", "supplier", "is_available"])]
