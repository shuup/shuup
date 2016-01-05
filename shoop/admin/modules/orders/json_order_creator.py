# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from copy import deepcopy

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext as _

from shoop.core.models import (
    CompanyContact, Contact, MutableAddress, OrderLineType, OrderStatus,
    PaymentMethod, PersonContact, Product, ShippingMethod, Shop
)
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

        is_product = bool(sline.get("type") == "product")
        price_val = sline.pop("baseUnitPrice", None) if is_product else sline.pop("unitPrice", None)
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

        discount_val = sline.pop("discountAmount", parse_decimal_string(str("0.00")))
        try:
            sl_kwargs["discount_amount"] = source.create_price(parse_decimal_string(discount_val))
        except Exception as exc:
            msg = _("The discount '%(discount)s' (for line %(text)s is invalid (%(error)s)") % {
                "discount": discount_val,
                "text": sl_kwargs["text"],
                "error": exc
            }
            self.add_error(ValidationError(msg, code="invalid_discount"))

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
        supplier = shop_product.suppliers.first()  # TODO: Allow setting a supplier?
        is_orderable = True
        for message in shop_product.get_orderability_errors(
                supplier=supplier, quantity=sl_kwargs["quantity"], customer=source.customer):
            self.add_error(ValidationError((_("Product %(product)s is not orderable: %(error)s") % {
                "product": product,
                "error": str(message.args[0])
            }), code=str(message.args[1])))
            is_orderable = False

        if not is_orderable:
            return False

        sl_kwargs["product"] = product
        sl_kwargs["supplier"] = supplier
        sl_kwargs["type"] = OrderLineType.PRODUCT
        sl_kwargs["sku"] = product.sku
        sl_kwargs["text"] = product.name
        return True

    def _add_json_line_to_source(self, source, sline):
        valid = True
        type = sline.get("type")
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
            source.add_line(**sl_kwargs)

    def _process_lines(self, source, state):
        state_lines = state.pop("lines", [])
        if not state_lines:
            self.add_error(ValidationError(_("Please add lines to the order."), code="no_lines"))
        for sline in state_lines:
            try:
                self._add_json_line_to_source(source, sline)
            except Exception as exc:  # pragma: no cover
                self.add_error(exc)

    def _create_contact_from_address(self, billing_address, is_company):
        name = billing_address.get("name", None)
        if not name:
            self.add_error(
                ValidationError(_("Name is required for customer"), code="no_name")
            )
            return

        phone = billing_address.get("phone", "")
        email = billing_address.get("email", "")
        fields = {"name": name, "phone": phone, "email": email}
        if is_company:
            tax_number = billing_address.get("tax_number", None)
            if not tax_number:
                self.add_error(
                    ValidationError(_("Tax number is not set for company."), code="no_tax_number")
                )
                return

            fields.update({"tax_number": tax_number})
            customer = CompanyContact(**fields)
        else:
            customer = PersonContact(**fields)
        return customer

    def _initialize_source_from_state(self, state, creator, save):
        shop_data = state.pop("shop", None).get("selected", {})
        shop = self.safe_get_first(Shop, pk=shop_data.pop("id", None))
        if not shop:
            self.add_error(ValidationError(_("Please choose a valid shop."), code="no_shop"))
            return None

        source = OrderSource(shop=shop)

        customer_data = state.pop("customer", None)
        billing_address_data = customer_data.pop("billingAddress", {})
        shipping_address_data = (
            billing_address_data
            if customer_data.pop("shipToBillingAddress", False)
            else customer_data.pop("shippingAddress", {}))
        is_company = customer_data.pop("isCompany", False)
        save_address = customer_data.pop("saveAddress", False)
        customer = self.safe_get_first(Contact, pk=customer_data.get("id")) if customer_data else None
        if not customer:
            customer = self._create_contact_from_address(billing_address_data, is_company)
            if not customer:
                return
            if save:
                customer.save()

        billing_address = MutableAddress.from_data(billing_address_data)
        shipping_address = MutableAddress.from_data(shipping_address_data)
        if save:
            billing_address.save()
            shipping_address.save()

        if save and save_address:
            customer.default_billing_address = billing_address
            customer.default_shipping_address = shipping_address
            customer.save()

        methods_data = state.pop("methods", None) or {}
        shipping_method = methods_data.pop("shippingMethod")
        if not shipping_method:
            self.add_error(ValidationError(_("Please select shipping method."), code="no_shipping_method"))

        payment_method = methods_data.pop("paymentMethod")
        if not payment_method:
            self.add_error(ValidationError(_("Please select payment method."), code="no_payment_method"))

        if self.errors:
            return

        source.update(
            creator=creator,
            customer=customer,
            billing_address=billing_address,
            shipping_address=shipping_address,
            status=OrderStatus.objects.get_default_initial(),
            shipping_method=self.safe_get_first(ShippingMethod, pk=shipping_method.get("id")),
            payment_method=self.safe_get_first(PaymentMethod, pk=payment_method.get("id")),
        )
        return source

    def _postprocess_order(self, order, state):
        comment = (state.pop("comment", None) or "")
        if comment:
            order.add_log_entry(comment, kind=LogEntryKind.NOTE, user=order.creator)

    def create_source_from_state(self, state, creator=None, save=False):
        """
        Create an order source from a state dict unserialized from JSON.

        :param state: State dictionary
        :type state: dict
        :param creator: Creator user
        :type creator: django.contrib.auth.models.User|None
        :param save: Flag whether order customer and addresses is saved to database
        :type save: boolean
        :return: The created order source, or None if something failed along the way
        :rtype: OrderSource|None
        """
        if not self.is_valid:  # pragma: no cover
            raise ValueError("Create a new JsonOrderCreator for each order.")
        # We'll be mutating the state to make it easier to track we've done everything,
        # so it's nice to deepcopy things first.
        state = deepcopy(state)

        # First, initialize an OrderSource.
        source = self._initialize_source_from_state(state, creator, save)
        if not source:
            return None

        # Then, copy some lines into it.
        self._process_lines(source, state)
        if not self.is_valid:  # If we encountered any errors thus far, don't bother going forward
            return None

        return source

    def create_order_from_state(self, state, creator=None):
        """
        Create an order from a state dict unserialized from JSON.

        :param state: State dictionary
        :type state: dict
        :param creator: Creator user
        :type creator: django.contrib.auth.models.User|None
        :return: The created order, or None if something failed along the way
        :rtype: Order|None
        """
        source = self.create_source_from_state(state, creator, save=True)

        # Then create an OrderCreator and try to get things done!
        creator = OrderCreator(request=None)
        try:
            order = creator.create_order(order_source=source)
            self._postprocess_order(order, state)
            return order
        except Exception as exc:  # pragma: no cover
            self.add_error(exc)
            return
