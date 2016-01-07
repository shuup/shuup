# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals, with_statement

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, EnumIntegerField
from jsonfield import JSONField
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from shoop.core.fields import InternalIdentifierField
from shoop.core.modules import ModuleInterface
from shoop.core.taxing import TaxableItem
from shoop.front.signals import get_method_validation_errors
from shoop.utils.text import force_ascii

from ._order_lines import OrderLineType

__all__ = ("MethodType", "ShippingMethod", "PaymentMethod", "MethodStatus")


class MethodType(Enum):
    SHIPPING = 1
    PAYMENT = 2

    class Labels:
        SHIPPING = _('shipping')
        PAYMENT = _('payment')


class MethodStatus(Enum):
    DISABLED = 0
    ENABLED = 1

    class Labels:
        DISABLED = _('disabled')
        ENABLED = _('enabled')


class MethodQuerySet(TranslatableQuerySet):
    def enabled(self):
        return self.filter(status=MethodStatus.ENABLED)

    def available_ids(self, shop, products):
        """
        Retrieve the common, available methods for a given shop and
        product IDs.

        :param shop_id: Shop ID
        :type shop_id: int
        :param product_ids: Product IDs
        :type product_ids: set[int]
        :return: Set of method IDs
        :rtype: set[int]
        """
        from ._product_shops import ShopProduct
        shop_product_m2m = self.model.shop_product_m2m
        shop_product_limiter_attr = "limit_%s" % self.model.shop_product_m2m

        limiting_products_query = {
            "shop": shop,
            "product__in": products,
            shop_product_limiter_attr: True
        }

        available_method_ids = set(self.enabled().values_list("pk", flat=True))

        for shop_product in ShopProduct.objects.filter(**limiting_products_query):
            available_method_ids &= set(getattr(shop_product, shop_product_m2m).values_list("pk", flat=True))
            if not available_method_ids:  # Out of IDs, better just fail fast
                break

        return available_method_ids

    def available(self, shop, products):
        return self.filter(pk__in=self.available_ids(shop, products))


@python_2_unicode_compatible
class Method(TaxableItem, ModuleInterface, TranslatableModel):
    tax_class = models.ForeignKey("TaxClass", verbose_name=_('tax class'), on_delete=models.PROTECT)
    status = EnumIntegerField(MethodStatus, db_index=True, default=MethodStatus.ENABLED, verbose_name=_('status'))
    identifier = InternalIdentifierField(unique=True)
    module_identifier = models.CharField(max_length=64, blank=True, verbose_name=_('module'))
    module_data = JSONField(blank=True, null=True, verbose_name=_('module data'))

    objects = MethodQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):  # pragma: no cover
        return (self.safe_translation_getter("name", any_language=True) or self.identifier or "")

    def get_source_lines(self, source):
        for line in self.module.get_source_lines(source=source):
            yield line

    def get_validation_errors(self, source):
        for receiver, errors in get_method_validation_errors.send(sender=Method, method=self, source=source):
            for error in errors:
                yield error
        for error in self.module.get_validation_errors(source=source):
            yield error

    def is_valid_for_source(self, source):
        for error in self.get_validation_errors(source):
            return False
        return True

    def get_effective_price_info(self, source):
        return self.module.get_effective_price_info(source=source)

    def get_effective_name(self, source):
        return self.module.get_effective_name(source=source)

    def __repr__(self):
        identifier = force_ascii(getattr(self, 'identifier', ''))
        return '<%s: %s "%s">' % (type(self).__name__, self.pk, identifier)


class ShippingMethod(Method):
    type = MethodType.SHIPPING
    line_type = OrderLineType.SHIPPING
    default_module_spec = "shoop.core.methods.default:DefaultShippingMethodModule"
    module_provides_key = "shipping_method_module"
    shop_product_m2m = "shipping_methods"

    translations = TranslatedFields(
        name=models.CharField(verbose_name=_('name'), max_length=64),
    )

    class Meta:
        verbose_name = _('shipping method')
        verbose_name_plural = _('shipping methods')


class PaymentMethod(Method):
    type = MethodType.PAYMENT
    line_type = OrderLineType.PAYMENT
    default_module_spec = "shoop.core.methods.default:DefaultPaymentMethodModule"
    module_provides_key = "payment_method_module"
    shop_product_m2m = "payment_methods"

    translations = TranslatedFields(
        name=models.CharField(verbose_name=_('name'), max_length=64),
    )

    class Meta:
        verbose_name = _('payment method')
        verbose_name_plural = _('payment methods')

    def get_payment_process_response(self, order, urls):
        return self.module.get_payment_process_response(order=order, urls=urls)

    def process_payment_return_request(self, order, request):
        return self.module.process_payment_return_request(order=order, request=request)
