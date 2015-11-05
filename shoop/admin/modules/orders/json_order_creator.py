# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from copy import deepcopy

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext as _

from shoop.core.models import Contact, OrderLineType, OrderStatus, PaymentMethod, Product, ShippingMethod, Shop
from shoop.core.order_creator import OrderCreator, OrderSource
from shoop.utils.analog import LogEntryKind
from shoop.utils.numbers import parse_decimal_string


class JsonOrderCreator(object):

    def __init__(self):
        self._errors = []

    @staticmethod
    def safe_get_first(model, **lookup):
        # A little helper function to clean up the code below.
        return model.objects.filter(**lookup).first()

    def add_error(self, error):
        self._errors.append(error)

    @property
    def is_valid(self):
        return not self._errors

    @property
    def errors(self):
        return tuple(self._errors)

    def _process_line_quantity_and_price(self, source, sline, sl_kwargs):
        quantity_val = sline.pop("quantity", None)
        try:
            sl_kwargs["quantity"] = parse_decimal_string(quantity_val)
        except Exception as exc:
            msg = _("The quantity '%(quantity)s' (for line %(text)s) is invalid (%(error)s)") % {
                "text": sl_kwargs["text"],
                "quantity": quantity_val,
                "error": exc,
            }
            self.add_error(ValidationError(msg, code="invalid_quantity"))
            return False

        price_val = sline.pop("unitPrice", None)
        try:
            sl_kwargs["base_unit_price"] = source.create_price(parse_decimal_string(price_val))
        except Exception as exc:
            msg = _("The price '%(price)s' (for line %(text)s) is invalid (%(error)s)") % {
                "text": sl_kwargs["text"],
                "price": price_val,
                "error": exc
            }
            self.add_error(ValidationError(msg, code="invalid_price"))
            return False
        return True

    def _process_product_line(self, source, sline, sl_kwargs):
        product_info = sline.pop("product", None)
        if not product_info:
            self.add_error(ValidationError(_("Product line does not have a product set."), code="no_product"))
            return False
        product = self.safe_get_first(Product, pk=product_info["id"])
        if not product:
            self.add_error(ValidationError(_("Product %s does not exist.") % product_info["id"], code="no_product"))
            return False
        try:
            shop_product = product.get_shop_instance(source.shop)
        except ObjectDoesNotExist:
            self.add_error(ValidationError((_("Product %(product)s is not available in the %(shop)s shop.") % {
                "product": product,
                "shop": source.shop
            }), code="no_shop_product"))
            return False
        sl_kwargs["product"] = product
        sl_kwargs["supplier"] = shop_product.suppliers.first()  # TODO: Allow setting a supplier?
        sl_kwargs["type"] = OrderLineType.PRODUCT
        sl_kwargs["sku"] = product.sku
        sl_kwargs["text"] = product.name
        return True

    def convert_json_line_to_source_line(self, source, sline):
        valid = True
        type = sline.pop("type")
        sl_kwargs = dict(
            line_id=sline.pop("id"),
            sku=sline.pop("sku", None),
            text=sline.pop("text", None),
            shop=source.shop,
            type=OrderLineType.OTHER  # Overridden in the `product` branch
        )

        if type != "text":
            if not self._process_line_quantity_and_price(source, sline, sl_kwargs):
                valid = False

        if type == "product":
            if not self._process_product_line(source, sline, sl_kwargs):
                valid = False

        if valid:
            return source.add_line(**sl_kwargs)
        else:
            return None

    def create_order_from_state(self, state, creator=None):
        if not self.is_valid:  # pragma: no cover
            raise ValueError("Create a new JsonOrderCreator for each order.")
        # We'll be mutating the state to make it easier to track we've done everything,
        # so it's nice to deepcopy things first.
        state = deepcopy(state)
        customer_data = state.pop("customer", None) or {}
        shop_data = state.pop("shop", None) or {}
        methods_data = state.pop("methods", None) or {}
        customer = self.safe_get_first(Contact, pk=customer_data.get("id"))
        if not customer:
            self.add_error(ValidationError(_("Please choose a valid customer."), code="no_customer"))
        shop = self.safe_get_first(Shop, pk=shop_data.pop("id", None))
        if not shop:
            self.add_error(ValidationError(_("Please choose a valid shop."), code="no_shop"))
            return None
        state_lines = state.pop("lines", [])
        source = OrderSource(shop=shop)
        source.creator = creator
        source.customer = customer
        source.status = OrderStatus.objects.get_default_initial()
        source.shipping_method = self.safe_get_first(ShippingMethod, pk=methods_data.pop("shippingMethodId"))
        source.payment_method = self.safe_get_first(PaymentMethod, pk=methods_data.pop("paymentMethodId"))
        for sline in state_lines:
            try:
                self.convert_json_line_to_source_line(source, sline)
            except Exception as exc:  # pragma: no cover
                self.add_error(exc)
        if not self.is_valid:  # If we encountered any errors thus far, don't bother going forward
            return None
        creator = OrderCreator(request=None)
        try:
            order = creator.create_order(order_source=source)
            comment = (state.pop("comment", None) or "")
            if comment:
                order.add_log_entry(comment, kind=LogEntryKind.NOTE, user=order.creator)
            return order
        except Exception as exc:  # pragma: no cover
            self.add_error(exc)
            return
