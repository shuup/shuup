# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField

from shuup.core.fields import MoneyValueField
from shuup.utils.properties import MoneyPropped, PriceProperty


class WeekDay(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6

    class Labels:
        Monday = _("Monday")
        Tuesday = _("Tuesday")
        Wednesday = _("Wednesday")
        Thursday = _("Thursday")
        Friday = _("Friday")
        Saturday = _("Saturday")
        Sunday = _("Sunday")


class ProductCatalogPriceRule(models.Model):
    """
    Store rules for catalog prices
    """

    module_identifier = models.CharField(max_length=100, verbose_name=_("Pricing module identifier"))
    contact_group = models.ForeignKey(
        "shuup.ContactGroup", related_name="catalog_prices", on_delete=models.CASCADE, null=True, editable=False
    )
    contact = models.ForeignKey(
        "shuup.Contact", related_name="catalog_prices", on_delete=models.CASCADE, null=True, editable=False
    )

    class Meta:
        unique_together = ("module_identifier", "contact_group", "contact")


class ProductCatalogPrice(MoneyPropped, models.Model):
    """
    Index the prices of products.
    There can be multiple prices, the best price will be selected.
    """

    id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(
        "shuup.Product", related_name="catalog_prices", on_delete=models.CASCADE, editable=False
    )
    shop = models.ForeignKey("shuup.Shop", related_name="catalog_prices", on_delete=models.CASCADE, editable=False)
    supplier = models.ForeignKey(
        "shuup.Supplier", related_name="catalog_prices", on_delete=models.CASCADE, editable=False
    )
    price = PriceProperty("price_value", "shop.currency", "shop.prices_include_tax")
    price_value = MoneyValueField(editable=False, verbose_name=_("price"), help_text=_("The indexed product price"))
    is_available = models.BooleanField(
        verbose_name=_("is available"),
        default=False,
        db_index=True,
        editable=False,
        help_text=_("Whether the product is available for purchasing. This status is managed by the supplier module."),
    )
    catalog_rule = models.ForeignKey(
        ProductCatalogPriceRule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Catalog rule"),
        help_text=_("The rule in which this price is available."),
    )

    def __str__(self):
        return f"{self.product} ({self.shop}, {self.supplier}) = {self.price}"

    class Meta:
        unique_together = ("product", "shop", "supplier", "catalog_rule")


class ProductCatalogDiscountedPriceRule(models.Model):
    """
    Store rules for discounted prices
    """

    module_identifier = models.CharField(max_length=100, verbose_name=_("Discount module identifier"))
    contact_group = models.ForeignKey(
        "shuup.ContactGroup",
        related_name="catalog_discounted_prices",
        on_delete=models.CASCADE,
        null=True,
        editable=False,
    )
    contact = models.ForeignKey(
        "shuup.Contact", related_name="catalog_discounted_prices", on_delete=models.CASCADE, null=True, editable=False
    )
    valid_start_date = models.DateTimeField(verbose_name=_("Valid start date and time"), null=True, blank=True)
    valid_end_date = models.DateTimeField(verbose_name=_("Valid end date and time"), null=True, blank=True)
    valid_start_hour = models.TimeField(verbose_name=_("Valid start hour"), null=True, blank=True)
    valid_end_hour = models.TimeField(verbose_name=_("Valid end hour"), null=True, blank=True)
    valid_weekday = EnumIntegerField(WeekDay, verbose_name=_("Valid weekday"), null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["module_identifier", "contact_group", "contact"]),
            models.Index(
                fields=["valid_start_date", "valid_end_date", "valid_start_hour", "valid_end_hour", "valid_weekday"]
            ),
        ]


class ProductCatalogDiscountedPrice(MoneyPropped, models.Model):
    """
    Index the discounted prices of products.
    There can be multiple discounted prices, the best discounted price will be selected.
    """

    id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(
        "shuup.Product", related_name="catalog_discounted_prices", on_delete=models.CASCADE, editable=False
    )
    shop = models.ForeignKey(
        "shuup.Shop", related_name="catalog_discounted_prices", on_delete=models.CASCADE, editable=False
    )
    supplier = models.ForeignKey(
        "shuup.Supplier", related_name="catalog_discounted_prices", on_delete=models.CASCADE, editable=False
    )
    discounted_price = PriceProperty("discounted_price_value", "shop.currency", "shop.prices_include_tax")
    discounted_price_value = MoneyValueField(
        editable=False,
        verbose_name=_("discounted price"),
        help_text=_("The indexed discounted product price."),
        null=True,
    )
    catalog_rule = models.ForeignKey(
        ProductCatalogDiscountedPriceRule,
        on_delete=models.CASCADE,
        verbose_name=_("Catalog rule"),
        help_text=_("The rule in which this discounted price is available."),
    )

    def __str__(self):
        return f"{self.product} ({self.shop}, {self.supplier}) = {self.discounted_price}"

    class Meta:
        unique_together = ("product", "shop", "supplier", "catalog_rule")
