# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from decimal import Decimal

import six
from django import forms
from django.core.exceptions import ValidationError
from django.http.response import HttpResponseRedirect
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _

from shoop.core.models import PaymentStatus
from shoop.core.pricing import PriceInfo


class BaseMethodModule(object):
    """
    Base method module implementation.
    """

    checkout_phase_class = None

    identifier = None
    name = None
    admin_detail_view_class = None
    option_fields = [
        ("price", forms.DecimalField(
            initial=0,
            label=_('Price'),
        )),
        ("price_waiver_product_minimum", forms.DecimalField(
            label=_('Waiver minimum'),
            help_text=_(
                'Waive the price when the total price of products '
                'in the order reaches this amount'
            ),
            initial=0
        )),
    ]

    def __init__(self, method, options):
        """
        :type method: shoop.core.models.Method
        :type options: dict
        """
        self.method = method
        self.options = options

    def get_options(self):
        data = self.options
        if self.option_fields:
            # If we have declared `option_fields`, use them to create a faux form that provides data validation and
            # transformation over the string-form data stored in the database.

            class_name = "%sOptionForm" % self.__class__.__name__
            if six.PY2:  # pragma: no cover
                class_name = force_bytes(class_name, errors="ignore")

            form = (
                type(
                    class_name,
                    (forms.BaseForm,),
                    {"base_fields": dict(self.option_fields)}
                )
            )(data=data)
            form.full_clean()
            data.update(getattr(form, "cleaned_data", {}))
        return data

    def get_validation_errors(self, source, **kwargs):
        """
        Return an iterable of human-readable errors (either Django's `ValidationError`s
        or just plain old strings) if there are any errors that would prevent using
        this method with a given `source`.

        This (instead of raising an error) broadly follows the Notification pattern.
        http://martinfowler.com/eaaDev/Notification.html

        :param source: source object
        :param kwargs: Other kwargs for future expansion
        :return: Iterable of errors
        :rtype: Iterable[str]
        """
        return ()

    def _is_price_waived(self, source):
        """
        Figure out whether any price should be waived for the given source.

        Meant for internal use by other module impls, hence the underscore.

        :param source: source
        :type source: shoop.core.order_creator.OrderSource
        :return: Boolean of waiver
        :rtype: bool
        """
        options = self.get_options()
        waive_limit_value = options.get("price_waiver_product_minimum")

        if waive_limit_value and waive_limit_value > 0:
            assert isinstance(waive_limit_value, Decimal)
            waive_limit = source.create_price(waive_limit_value)
            product_total = source.total_price_of_products
            if not product_total:
                return False
            return (product_total >= waive_limit)
        return False

    def get_effective_price_info(self, source, **kwargs):
        """
        Get price of this method for given OrderSource.

        :param source: source object
        :type source: shoop.core.order_creator.OrderSource
        :param kwargs: Other kwargs for future expansion
        :rtype: shoop.core.pricing.PriceInfo
        """
        price_value = self.get_options().get("price", 0)
        normal_price = source.shop.create_price(price_value)
        if self._is_price_waived(source):
            return PriceInfo(source.shop.create_price(0), normal_price, 1)
        return PriceInfo(normal_price, normal_price, 1)

    def get_effective_name(self, source, **kwargs):
        """
        Return the effective name for this method. Useful to add shipping mode ("letter", "parcel") for instance.

        :param source: source object
        :type source: shoop.core.order_creator.OrderSource
        :param kwargs: Other kwargs for future expansion
        :return: name
        :rtype: unicode
        """

        try:
            return self.method.name
        except:
            return six.text_type(self)

    def get_source_lines(self, source):
        from shoop.core.order_creator import SourceLine

        price_info = self.get_effective_price_info(source)
        assert price_info.quantity == 1
        yield SourceLine(
            source=source,
            quantity=1,
            type=self.method.line_type,
            text=self.get_effective_name(source),
            base_unit_price=price_info.base_unit_price,
            discount_amount=price_info.discount_amount,
            tax_class=self.method.tax_class,
        )


class BaseShippingMethodModule(BaseMethodModule):
    """
    Base shipping method module implementation.
    """

    no_lower_limit_text = _('0 or below: no lower limit')

    option_fields = BaseMethodModule.option_fields + [
        ("min_weight", forms.DecimalField(label=_('minimum weight'), initial=0, help_text=no_lower_limit_text)),
        ("max_weight", forms.DecimalField(label=_('maximum weight'), initial=0, help_text=no_lower_limit_text)),
    ]

    def get_validation_errors(self, source, **kwargs):
        weight = sum(((l.get("weight") or 0) for l in source.get_lines()), 0)
        options = self.get_options()

        min_weight = options.get("min_weight")

        if min_weight:
            assert isinstance(min_weight, Decimal)
            if min_weight > 0 and weight < min_weight:
                yield ValidationError(_("Minimum weight not met."), code="min_weight")

        max_weight = options.get("max_weight")

        if max_weight:
            assert isinstance(max_weight, Decimal)
            if max_weight > 0 and weight > max_weight:
                yield ValidationError(_("Maximum weight exceeded."), code="max_weight")


class BasePaymentMethodModule(BaseMethodModule):
    """
    Base payment method module implementation.
    """

    def get_payment_process_response(self, order, urls):
        return HttpResponseRedirect(urls["return"])  # Directly return to wherever we want to.

    def process_payment_return_request(self, order, request):
        if order.payment_status == PaymentStatus.NOT_PAID:
            order.payment_status = PaymentStatus.DEFERRED
            order.add_log_entry("Payment status set to deferred by %s" % self.method)
            order.save(update_fields=("payment_status",))
