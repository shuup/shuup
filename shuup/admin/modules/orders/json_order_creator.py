# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from copy import deepcopy
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from shuup.core.models import (
    CompanyContact,
    Contact,
    MutableAddress,
    OrderLineType,
    OrderStatus,
    PaymentMethod,
    PersonContact,
    Product,
    ShippingMethod,
    Shop,
    ShopProduct,
    Supplier,
)
from shuup.core.order_creator import OrderCreator, OrderModifier, OrderSource
from shuup.core.order_creator._source import LineSource
from shuup.utils.analog import LogEntryKind
from shuup.utils.numbers import nickel_round, parse_decimal_string


class AdminOrderSource(OrderSource):
    def get_validation_errors(self):
        return []

    def is_cash_order(self):
        return self.payment_method and self.payment_method.choice_identifier == "cash"


class AdminOrderCreator(OrderCreator):
    def _check_orderability(self, order_line):
        return


class AdminOrderModifier(OrderModifier):
    def _check_orderability(self, order_line):
        return


class JsonOrderCreator(object):
    def __init__(self):
        self._errors = []

    @staticmethod
    def safe_get_first(model, **lookup):
        # A little helper function to clean up the code below.
        return model.objects.filter(**lookup).first()

    @staticmethod
    def is_empty_address(address_data):
        """An address will have at least a tax_number field. It will still be considered empty."""
        return list(address_data.keys()) == ["tax_number"]

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
            msg = _("The quantity '%(quantity)s' (for line %(text)s) is invalid (%(error)s).") % {
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
            msg = _("The price '%(price)s' (for line %(text)s) is invalid (%(error)s).") % {
                "text": sl_kwargs["text"],
                "price": price_val,
                "error": exc,
            }
            self.add_error(ValidationError(msg, code="invalid_price"))
            return False

        discount_val = sline.pop("discountAmount", parse_decimal_string(str("0.00")))
        try:
            sl_kwargs["discount_amount"] = source.create_price(parse_decimal_string(discount_val))
        except Exception as exc:
            msg = _("The discount '%(discount)s' (for line %(text)s is invalid (%(error)s).") % {
                "discount": discount_val,
                "text": sl_kwargs["text"],
                "error": exc,
            }
            self.add_error(ValidationError(msg, code="invalid_discount"))

        return True

    def _process_product_line(self, source, sline, sl_kwargs):
        product_info = sline.pop("product", None)
        supplier_info = sline.pop("supplier", None)

        if not supplier_info:
            self.add_error(ValidationError(_("Product line does not have a supplier."), code="no_supplier"))
            return False

        if not product_info:
            self.add_error(ValidationError(_("Product line does not have a product set."), code="no_product"))
            return False
        product = self.safe_get_first(Product, pk=product_info["id"])
        if not product:
            self.add_error(ValidationError(_("Product `%s` does not exist.") % product_info["id"], code="no_product"))
            return False
        try:
            shop_product = product.get_shop_instance(source.shop)
        except ShopProduct.DoesNotExist:
            self.add_error(
                ValidationError(
                    (
                        _("Product %(product)s is not available in the %(shop)s shop.")
                        % {"product": product, "shop": source.shop}
                    ),
                    code="no_shop_product",
                )
            )
            return False

        supplier = self.safe_get_first(Supplier, pk=supplier_info["id"])

        if not supplier:
            supplier = shop_product.get_supplier(source.customer, sl_kwargs["quantity"], source.shipping_address)

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
            type=OrderLineType.OTHER,  # Overridden in the `product` branch
        )

        # _process_product_line pops this value, so need to store it here
        supplier_info = sline.get("supplier")

        if type != "text":
            if not self._process_line_quantity_and_price(source, sline, sl_kwargs):
                valid = False

        if type == "product":
            if not self._process_product_line(source, sline, sl_kwargs):
                valid = False
        else:
            if supplier_info:
                supplier = self.safe_get_first(Supplier, pk=supplier_info["id"])
                if supplier:
                    sl_kwargs["supplier"] = supplier

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
        phone = billing_address.get("phone", "")
        email = billing_address.get("email", "")
        fields = {"name": name, "phone": phone, "email": email}
        if is_company:
            tax_number = billing_address.get("tax_number", None)
            fields.update({"tax_number": tax_number})
            customer = CompanyContact(**fields)
        else:
            customer = PersonContact(**fields)
        return customer

    def _get_address(self, address, is_company, save):
        if self.is_empty_address(address):
            return None
        address_form = forms.modelform_factory(MutableAddress, exclude=[])
        address_form_instance = address_form(data=address)
        address_form_instance.full_clean()
        if not address_form_instance.is_valid():
            for field_name, errors in address_form_instance.errors.items():
                field_label = address_form_instance.fields[field_name].label
                for error_msg in errors:
                    self.add_error(
                        ValidationError(
                            "Error! %(field_label)s: %(error_msg)s"
                            % {"field_label": field_label, "error_msg": error_msg},
                            code="invalid_address",
                        )
                    )
            return None
        if is_company and not address_form_instance.cleaned_data["tax_number"]:
            self.add_error(ValidationError(_("Tax number is not set for company."), code="no_tax_number"))
            return None
        if save:
            return address_form_instance.save()
        return MutableAddress.from_data(address_form_instance.cleaned_data)

    def _initialize_source_from_state(self, state, creator, ip_address, save, order_to_update=None):
        shop_data = state.pop("shop", None).get("selected", {})
        shop = self.safe_get_first(Shop, pk=shop_data.pop("id", None))
        if not shop:
            self.add_error(ValidationError(_("Please choose a valid shop."), code="no_shop"))
            return None

        source = AdminOrderSource(shop=shop)
        if order_to_update:
            source.update_from_order(order_to_update)

        customer_data = state.pop("customer", {})
        billing_address_data = customer_data.pop("billingAddress", {})
        shipping_address_data = (
            billing_address_data
            if customer_data.pop("shipToBillingAddress", False)
            else customer_data.pop("shippingAddress", {})
        )
        is_company = customer_data.pop("isCompany", False)
        save_address = customer_data.pop("saveAddress", False)

        billing_address = None
        shipping_address = None
        customer = None

        if customer_data:
            customer = self._get_customer(customer_data, billing_address_data, is_company, save)
            billing_address = self._get_address(billing_address_data, is_company, save)
            if self.errors:
                return
            shipping_address = self._get_address(shipping_address_data, is_company, save)
            if self.errors:
                return

            if save and save_address:
                customer.default_billing_address = billing_address
                customer.default_shipping_address = shipping_address
                customer.save()

        methods_data = state.pop("methods", None) or {}
        shipping_method = methods_data.pop("shippingMethod")
        if not shipping_method and settings.SHUUP_ADMIN_REQUIRE_SHIPPING_METHOD_AT_ORDER_CREATOR:
            self.add_error(ValidationError(_("Please select shipping method."), code="no_shipping_method"))

        payment_method = methods_data.pop("paymentMethod")
        if not payment_method and settings.SHUUP_ADMIN_REQUIRE_PAYMENT_METHOD_AT_ORDER_CREATOR:
            self.add_error(ValidationError(_("Please select payment method."), code="no_payment_method"))

        if self.errors:
            return

        source.update(
            creator=creator,
            ip_address=ip_address,
            customer=customer,
            billing_address=billing_address,
            shipping_address=shipping_address,
            status=OrderStatus.objects.get_default_initial(),
            shipping_method=(
                self.safe_get_first(ShippingMethod, pk=shipping_method.get("id")) if shipping_method else None
            ),
            payment_method=(
                self.safe_get_first(PaymentMethod, pk=payment_method.get("id")) if payment_method else None
            ),
        )
        return source

    def _get_customer(self, customer_data, billing_address_data, is_company, save):
        pk = customer_data.get("id")
        customer = self.safe_get_first(Contact, pk=pk) if customer_data and pk else None
        if not customer:
            customer = self._create_contact_from_address(billing_address_data, is_company)
            if not customer:
                return
            if save:
                customer.save()
        return customer

    def _postprocess_order(self, order, state):
        comment = state.pop("comment", None) or ""
        if comment:
            order.add_log_entry(comment, kind=LogEntryKind.NOTE, user=order.creator)

    def create_source_from_state(self, state, creator=None, ip_address=None, save=False, order_to_update=None):
        """
        Create an order source from a state dict unserialized from JSON.

        :param state: State dictionary.
        :type state: dict
        :param creator: Creator user.
        :type creator: django.contrib.auth.models.User|None
        :param save: Flag whether order customer and addresses is saved to database.
        :type save: boolean
        :param order_to_update: Order object to edit.
        :type order_to_update: shuup.core.models.Order|None
        :return: The created order source, or None if something failed along the way.
        :rtype: OrderSource|None
        """
        if not self.is_valid:  # pragma: no cover
            raise ValueError("Error! Create a new `JsonOrderCreator` for each order.")
        # We'll be mutating the state to make it easier to track we've done everything,
        # so it's nice to deepcopy things first.
        state = deepcopy(state)

        # First, initialize an OrderSource.
        source = self._initialize_source_from_state(
            state, creator=creator, ip_address=ip_address, save=save, order_to_update=order_to_update
        )
        if not source:
            return None

        # Then, copy some lines into it.
        self._process_lines(source, state)
        if not self.is_valid:  # If we encountered any errors thus far, don't bother going forward
            return None

        if order_to_update:
            for code in order_to_update.codes:
                source.add_code(code)

        if source.is_cash_order():
            processor = source.payment_method.payment_processor
            taxful_total = source.taxful_total_price
            rounded = nickel_round(
                taxful_total, quant=processor.rounding_quantize, rounding=processor.rounding_mode.value
            )
            remainder = rounded - taxful_total
            line_data = dict(
                line_id="rounding",
                type=OrderLineType.ROUNDING,
                quantity=1,
                shop=source.shop,
                text="Rounding",
                base_unit_price=source.create_price(remainder.value),
                tax_class=None,
                line_source=LineSource.ADMIN,
            )
            source.add_line(**line_data)
            source.get_final_lines()

        return source

    def create_order_from_state(self, state, creator=None, ip_address=None):
        """
        Create an order from a state dict unserialized from JSON.

        :param state: State dictionary.
        :type state: dict
        :param creator: Creator user.
        :type creator: django.contrib.auth.models.User|None
        :param ip_address: Remote IP address (IPv4 or IPv6).
        :type ip_address: str
        :return: The created order, or None if something failed along the way.
        :rtype: Order|None
        """
        source = self.create_source_from_state(state, creator=creator, ip_address=ip_address, save=True)

        if not source:
            return

        # Then create an OrderCreator and try to get things done!
        creator = AdminOrderCreator()
        try:
            order = creator.create_order(order_source=source)
            self._postprocess_order(order, state)
            return order
        except Exception as exc:  # pragma: no cover
            self.add_error(exc)
            return

    def update_order_from_state(self, state, order_to_update, modified_by=None):
        """
        Update an order from a state dict unserialized from JSON.

        :param state: State dictionary.
        :type state: dict
        :param order_to_update: Order object to edit.
        :type order_to_update: shuup.core.models.Order
        :return: The created order, or None if something failed along the way.
        :rtype: Order|None
        """
        # Collect ids for products that were removed from the order for stock update
        removed_product_ids = self.get_removed_product_ids(state, order_to_update)

        source = self.create_source_from_state(state, order_to_update=order_to_update, save=True)
        if source:
            source.modified_by = modified_by
        modifier = AdminOrderModifier()
        try:
            order = modifier.update_order_from_source(order_source=source, order=order_to_update)
            self._postprocess_order(order, state)
        except Exception as exc:
            self.add_error(exc)
            return

        # Update stock for products that were completely removed from the order
        if removed_product_ids:
            self.update_stock_for_removed_products(removed_product_ids, source.shop)

        return order

    def get_removed_product_ids(self, state, order_to_update):
        """
        Collect product ids for products which were removed from the order.

        :param state: State dictionary.
        :type state: dict
        :param order_to_update: Order object to edit.
        :type order_to_update: shuup.core.models.Order
        :return: set
        """

        current_lines = state.get("lines", [])
        current_product_ids = set()
        for line in current_lines:
            if line["type"] == "product" and line["product"] is not None:
                current_product_ids.add(line["product"]["id"])

        old_prod_ids = set()
        for line in order_to_update.lines.exclude(product_id=None):
            old_prod_ids.add(line.product.id)

        return old_prod_ids - current_product_ids

    def update_stock_for_removed_products(self, removed_ids, shop):
        """
        Update stocks for products which were completely removed from the updated order.

        :param removed_ids: Set of removed product ids.
        :type removed_ids: set
        :param shop: Shop instance where this order is made.
        :type shop: shuup.core.models.Shop
        """
        for prod_id in removed_ids:
            product = Product.objects.get(id=prod_id)
            shop_product = product.get_shop_instance(shop)
            for supplier in shop_product.suppliers.enabled():
                supplier.update_stock(product.id)
