# This file is part of Shuup.
#
# Copyright (c) 2012-2020, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import random
import string

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class CouponUsage(models.Model):
    coupon = models.ForeignKey(on_delete=models.CASCADE, to="discounts.CouponCode", related_name="usages")
    order = models.ForeignKey(on_delete=models.CASCADE, to="shuup.Order", related_name="discounts_coupon_usages")
    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))

    def __str__(self):
        return "Code %s for %s" % (self.coupon, self.order)

    @classmethod
    def add_usage(cls, order, coupon):
        return cls.objects.create(order=order, coupon=coupon)


@python_2_unicode_compatible
class CouponCode(models.Model):
    code = models.CharField(max_length=12)
    name_field = "code"

    shops = models.ManyToManyField("shuup.Shop", blank=True, verbose_name=_("shops"))
    usage_limit_customer = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("usage limit per customer"),
        help_text=_("Limit the amount of usages per a single customer."))
    usage_limit = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("usage limit"),
        help_text=_("Set the absolute limit of usages for this coupon. "
                    "If the limit is zero (0) coupon cannot be used."))
    active = models.BooleanField(default=True, verbose_name=_("active"))

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name="+", on_delete=models.SET_NULL, verbose_name=_("created by"))
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name="+", on_delete=models.SET_NULL, verbose_name=_("modified by"))

    created_on = models.DateTimeField(auto_now_add=True, editable=False, verbose_name=_("created on"))
    modified_on = models.DateTimeField(auto_now=True, editable=False, verbose_name=_("modified on"))

    def __str__(self):
        return self.code

    @classmethod
    def generate_code(cls, length=6):
        if length > 12:
            length = 12
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

    @property
    def exhausted(self):
        val = bool(self.usage_limit and self.usages.count() >= self.usage_limit)
        return val

    @property
    def attached(self):
        return self.coupon_code_discounts.all().exists()

    @classmethod
    def is_usable(cls, shop, code, customer):
        try:
            code = cls.objects.get(code__iexact=code, active=True, shops=shop)
            return code.can_use_code(shop, customer)
        except cls.DoesNotExist:
            return False

    def can_use_code(self, shop, customer):
        if not self.shops.filter(id=shop.pk).exists():
            return False

        if not self.active:
            return False

        if not self.attached:
            return False

        if self.usage_limit_customer:
            if not customer or customer.is_anonymous:
                return False
            if (self.usages.filter(order__customer=customer, coupon=self).count() >= self.usage_limit_customer):
                return False

        return not self.exhausted

    def use(self, order):
        return CouponUsage.add_usage(order=order, coupon=self)
