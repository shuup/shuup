# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from shuup.core.fields import InternalIdentifierField, MoneyValueField
from shuup.utils.properties import MoneyPropped


def _get_basic_available_query(for_datetime, shop=None):
    """
    Whether the discount is:
        1. Currently active or
        2. Potentially active in the future

    Here the start datetime doesn't matter since it can be
    either null, lower and greater than the
    datetime compared to and still be available. So we want
    discounts that is active and the end datetime is
    null or in future.
    """
    query = Q(Q(active=True) & (Q(end_datetime__isnull=True) | Q(end_datetime__gte=for_datetime)))

    if shop:
        query &= Q(shop=shop)

    return query


class DiscountQueryset(models.QuerySet):
    def active(self, shop=None):
        return self.filter(_get_basic_available_query(timezone.now(), shop))

    def archived(self, shop=None):
        shop_query = Q()  # Since the exclude returns active discounts for other shop too
        if shop:
            shop_query &= Q(shop=shop)

        return self.exclude(_get_basic_available_query(timezone.now(), shop)).filter(shop_query)

    def available(self, shop=None):
        user_current_datetime = timezone.localtime(timezone.now())
        user_current_weekday = user_current_datetime.weekday()
        user_current_time = user_current_datetime.time()

        query = Q(
            Q(active=True)
            & (Q(start_datetime__isnull=True) | Q(start_datetime__lte=user_current_datetime))
            & (Q(end_datetime__isnull=True) | Q(end_datetime__gte=user_current_datetime))
            & (
                Q(happy_hours__time_ranges__isnull=True)
                | Q(
                    happy_hours__time_ranges__weekday=user_current_weekday,
                    happy_hours__time_ranges__from_hour__lte=user_current_time,
                    happy_hours__time_ranges__to_hour__gt=user_current_time,
                )
            )
        )

        if shop:
            query &= Q(shop=shop)

        return self.filter(query)


@python_2_unicode_compatible
class Discount(models.Model, MoneyPropped):
    name = models.CharField(
        null=True,
        blank=True,
        max_length=120,
        verbose_name=_("name"),
        help_text=_("The name for this discount. Used internally with discount lists for filtering."),
    )
    shop = models.ForeignKey(
        "shuup.Shop", verbose_name=_("shop"), related_name="shop_discounts", on_delete=models.CASCADE
    )
    identifier = InternalIdentifierField(unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="discounts_created_by",
        on_delete=models.SET_NULL,
        verbose_name=_("created by"),
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="discounts_modified_by",
        on_delete=models.SET_NULL,
        verbose_name=_("modified by"),
    )
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_("modified on"))

    supplier = models.ForeignKey(
        on_delete=models.CASCADE,
        to="shuup.Supplier",
        related_name="supplier_discounts",
        null=True,
        blank=True,
        verbose_name=_("supplier"),
        help_text=_("Select supplier for this discount."),
    )
    active = models.BooleanField(
        default=True,
        verbose_name=_("active"),
        help_text=_("Enable this if the discount is currently active. Please also set a start and an end date."),
    )
    start_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("start date and time"),
        help_text=_(
            "The date and time the discount starts. This is only applicable if the discount is marked as active."
        ),
    )
    end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("end date and time"),
        help_text=_(
            "The date and time the discount ends. This is only applicable if the discount is marked as active."
        ),
    )
    happy_hours = models.ManyToManyField(
        "discounts.HappyHour",
        related_name="discounts",
        blank=True,
        verbose_name=_("happy hours"),
        help_text=_("Select happy hours for this discount."),
    )
    product = models.ForeignKey(
        "shuup.Product",
        related_name="product_discounts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("product"),
        help_text=_("Select product for this discount."),
    )
    exclude_selected_category = models.BooleanField(
        default=False,
        verbose_name=_("exclude selected category"),
        help_text=_("Exclude products in selected category from this discount."),
    )
    category = models.ForeignKey(
        "shuup.Category",
        related_name="category_discounts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("category"),
        help_text=_("Select category for this discount."),
    )
    contact = models.ForeignKey(
        "shuup.Contact",
        related_name="contact_discounts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("contact"),
        help_text=_("Select contact for this discount."),
    )
    contact_group = models.ForeignKey(
        "shuup.ContactGroup",
        related_name="contact_group_discounts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("contact group"),
        help_text=_("Select contact group for this discount."),
    )
    discounted_price_value = MoneyValueField(
        null=True,
        blank=True,
        verbose_name=_("discounted price"),
        help_text=_("Discounted product price for this discount."),
    )
    discount_amount_value = MoneyValueField(
        null=True,
        blank=True,
        verbose_name=_("discount amount"),
        help_text=_("Discount amount value for this discount."),
    )
    discount_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        blank=True,
        null=True,
        verbose_name=_("discount percentage"),
        help_text=_("Discount percentage for this discount."),
    )

    objects = DiscountQueryset.as_manager()

    def __str__(self):
        return self.name or self.identifier or "%s" % self.pk

    class Meta:
        verbose_name = _("product discount")
        verbose_name_plural = _("product discounts")

    def save(self, *args, **kwargs):
        super(Discount, self).save(*args, **kwargs)

    def clean(self):
        if self.active and (not self.start_datetime or not self.end_datetime):
            raise ValidationError(_("Start date and end date are required when the discount is active."))

        values = (self.discount_percentage, self.discount_amount_value, self.discounted_price_value)
        valid_values_count = len([v for v in values if v])
        if valid_values_count == 0 or valid_values_count > 1:
            raise ValidationError(
                _("Either discounted price or discount percentage or discount amount should be configured.")
            )
